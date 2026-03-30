from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import List

ws_router = APIRouter(prefix="/ws", tags=["ws"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, List[WebSocket]] = {}
        self.answers_buffer: dict[str, list[dict]] = {}

    async def connect(self, quiz_uuid: str, websocket: WebSocket):
        await websocket.accept()
        if quiz_uuid not in self.active_connections:
            self.active_connections[quiz_uuid] = []
            self.answers_buffer[quiz_uuid] = []
        self.active_connections[quiz_uuid].append(websocket)

    def disconnect(self, quiz_uuid: str, websocket: WebSocket):
        if quiz_uuid in self.active_connections:
            self.active_connections[quiz_uuid].remove(websocket)

    async def broadcast(self, quiz_uuid: str, message: dict):
        if quiz_uuid in self.active_connections:
            for connection in self.active_connections[quiz_uuid]:
                await connection.send_json(message)


manager = ConnectionManager()


@ws_router.websocket("/quiz/{quiz_uuid}")
async def quiz_ws(websocket: WebSocket, quiz_uuid: str):
    await manager.connect(quiz_uuid, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if quiz_uuid in manager.answers_buffer:
                manager.answers_buffer[quiz_uuid].append(data)

            await manager.broadcast(quiz_uuid, data)
    except WebSocketDisconnect:
        manager.disconnect(quiz_uuid, websocket)

        from src.models.answer import UserAnswer
        from src.db.session import AsyncSessionLocal

        answers_to_save = manager.answers_buffer.get(quiz_uuid, [])

        with AsyncSessionLocal() as session:
            for ans in answers_to_save:
                user_answer = UserAnswer(
                    user_id=ans["user_id"],
                    question_id=ans["question_id"],
                    answer_id=ans["answer_id"]
                )
                session.add(user_answer)
            await session.commit()

    manager.answers_buffer[quiz_uuid] = []

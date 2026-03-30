from celery import Celery

celery_app = Celery(
    "worker",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1"
)

celery_app.conf.task_routes = {
    "tasks.create_quiz_from_file_task": {"queue": "quiz_queue"}
}

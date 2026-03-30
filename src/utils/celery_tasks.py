from sqlalchemy.orm import sessionmaker
from src.core.celery_settings import celery_app
from src.db.session import engine
from src.models import Quiz, Question, Answer
from src.utils.parce_files import parse_xlsx, parse_docx, parse_pdf


SessionLocal = sessionmaker(bind=engine)

@celery_app.task
def create_quiz_from_file_task(file_path, user_id):
    if file_path.endswith(".xlsx"):
        quiz_title, questions = parse_xlsx(file_path)
    elif file_path.endswith(".docx"):
        quiz_title, questions = parse_docx(file_path)
    elif file_path.endswith(".pdf"):
        quiz_title, questions = parse_pdf(file_path)
    else:
        raise ValueError("Unsupported file type")

    with SessionLocal() as session:
        quiz = Quiz(title=quiz_title, author_id=user_id)
        session.add(quiz)
        session.flush()

        for question_text, answers_texts in questions:
            question = Question(title=question_text, quiz_id=quiz.id)
            session.add(question)
            session.flush()

            for i, ans_text in enumerate(answers_texts):
                answer = Answer(
                    title=ans_text,
                    is_true_answer=(i == 0),
                    question_id=question.id
                )
                session.add(answer)

        session.commit()

    return f"{len(questions)} questions added"

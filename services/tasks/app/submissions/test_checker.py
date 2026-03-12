from typing import Dict, List
from app.questions.models import Question
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.utils.enums import QuestionType


def calc_multiple_choice_score(
    correct: set[str],
    chosen: set[str],
) -> float:
    c = len(correct & chosen)
    w = len(chosen - correct)

    if not correct:
        return 0.0

    return max(0.0, (c - w) / len(correct))


async def check_test_submission(
    db: AsyncSession,
    task_id: str,
    answers: Dict[str, List[str]],
) -> tuple[int, int, Dict[str, List[str]]]:

    result = await db.execute(
        select(Question).where(Question.task_id == task_id).order_by(Question.order)
    )
    questions = result.scalars().all()

    score = 0.0
    max_score = len(questions)
    feedback = []

    for q in questions:
        user_answer = answers.get(str(q.id))
        score = 0.0

        if q.type == QuestionType.SHORT_ANSWER:
            if isinstance(user_answer, str):
                normalized = user_answer.strip().lower()
                correct = {a.lower() for a in q.correct_answers}
                if normalized in correct:
                    score = 1.0

        elif q.type == QuestionType.SINGLE_CHOICE:
            if user_answer == q.correct_answers[0]:
                score = 1.0

        elif q.type == QuestionType.MULTIPLE_CHOICE:
            chosen = set(user_answer) if user_answer else set()
            correct = set(q.correct_answers)
            score = calc_multiple_choice_score(correct, chosen)

        total_score += score

        feedback.append(
            {
                "question_id": q.id,
                "score": round(score, 3),
                "max": 1,
                "correct_answers": q.correct_answers or [],
                "user_answer": user_answer,
            }
        )

    grade_5 = (total_score / max_score) * 5 if max_score > 0 else 0

    return (
        round(total_score, 3),
        max_score,
        {
            "details": feedback,
            "grade_5": grade_5,
            "percentage": (
                round((total_score / max_score) * 100, 2) if max_score > 0 else 0
            ),
        },
    )

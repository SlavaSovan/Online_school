from typing import Dict, List, Set
from app.questions.models import Question
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.utils.enums import QuestionType


def calc_multiple_choice_score(
    correct: Set[str],
    chosen: Set[str],
) -> float:
    if not correct:
        return 0.0

    correct_count = len(correct & chosen)
    wrong_count = len(chosen - correct)

    return max(0.0, correct_count / (len(correct) + wrong_count))


async def check_test_submission(
    db: AsyncSession,
    task_id: str,
    answers: Dict[str, List[str]],
    task_max_score: int,
) -> tuple[float, Dict]:

    result = await db.execute(
        select(Question)
        .where(Question.task_id == task_id)
        .order_by(Question.order)
        .options(selectinload(Question.options))
    )
    questions = result.scalars().all()

    questions_count = len(questions)
    raw_score = 0.0
    feedback = []

    for q in questions:
        user_answer = answers.get(str(q.id))
        question_score = 0.0

        option_texts = {}
        if q.options:
            option_texts = {str(opt.id): opt.text for opt in q.options}

        user_answer_texts = []
        if user_answer:
            for answer_id in user_answer:
                text = option_texts.get(answer_id, answer_id)
                user_answer_texts.append(text)

        if q.question_type == QuestionType.SHORT_ANSWER:
            if user_answer and len(user_answer) > 0:
                normalized_answer = user_answer[0].strip().lower()
                correct_answers = [a.lower() for a in (q.correct_answers or [])]
                if normalized_answer in correct_answers:
                    question_score = 1.0

        elif q.question_type == QuestionType.SINGLE_CHOICE:
            if user_answer and len(user_answer) > 0:
                correct_option_ids = [
                    str(opt.id) for opt in q.options if opt.is_correct
                ]
                if user_answer[0] in correct_option_ids:
                    question_score = 1.0

        elif q.question_type == QuestionType.MULTIPLE_CHOICE:
            if user_answer and len(user_answer) > 0:
                chosen = set(user_answer)
                correct_option_ids = {
                    str(opt.id) for opt in q.options if opt.is_correct
                }
                question_score = calc_multiple_choice_score(correct_option_ids, chosen)

        raw_score += question_score

        feedback.append(
            {
                "question_id": q.id,
                "question_text": q.text,
                "question_type": q.question_type.value,
                "score": round(question_score, 3),
                "max_score": 1,
                "user_answer": user_answer_texts,
                "correct_answers": q.correct_answers
                or [opt.text for opt in q.options if opt.is_correct],
            }
        )

    if questions_count > 0:
        scaled_score = (raw_score / questions_count) * task_max_score
    else:
        scaled_score = 0

    percentage = (scaled_score / task_max_score * 100) if task_max_score > 0 else 0
    grade_5 = (scaled_score / task_max_score * 5) if task_max_score > 0 else 0

    return (
        round(scaled_score, 2),
        {
            "details": feedback,
            "grade_5": round(grade_5, 2),
            "percentage": round(percentage, 2),
            "total_score": round(scaled_score, 2),
            "max_score": task_max_score,
            "raw_score": round(raw_score, 2),
            "questions_count": questions_count,
        },
    )

"""
Dynamic quiz generation engine.

Replaces the old "return the whole fixed question bank" approach: every
call randomly samples from the question pool, so no two attempts (even
back to back) are guaranteed to look the same. Purely selection logic --
grading and diagnosis are untouched and still live in diagnosis_engine.py.
"""
import random

from sqlalchemy.orm import Session

from app.models.concept import Concept
from app.models.quiz import Question

EASY_MAX_DIFFICULTY = 2     # difficulty 1-2 -> Easy
MEDIUM_MAX_DIFFICULTY = 3   # difficulty 3   -> Medium
# difficulty 4-5 -> Hard

DEFAULT_MIX = {"easy": 3, "medium": 4, "hard": 3}  # matches the product spec's example mix


def _difficulty_tier(difficulty: int) -> str:
    if difficulty <= EASY_MAX_DIFFICULTY:
        return "easy"
    if difficulty <= MEDIUM_MAX_DIFFICULTY:
        return "medium"
    return "hard"


def generate_quiz(
    db: Session,
    subject: str | None = None,
    easy: int = DEFAULT_MIX["easy"],
    medium: int = DEFAULT_MIX["medium"],
    hard: int = DEFAULT_MIX["hard"],
    exclude_question_ids: list[int] | None = None,
) -> list[Question]:
    """Randomly selects `easy` + `medium` + `hard` questions.

    `subject` of None/"mixed" pulls from every subject; otherwise
    restricts to one subject ("dsa" | "python" | "sql" | "ml").

    `exclude_question_ids` lets the caller avoid repeating very recent
    questions for the same user (used by the Daily Spark feature).
    """
    query = db.query(Question).join(Concept, Question.concept_id == Concept.id)
    if subject and subject != "mixed":
        query = query.filter(Concept.subject == subject)

    all_questions = query.all()
    if exclude_question_ids:
        exclude_set = set(exclude_question_ids)
        pool = [q for q in all_questions if q.id not in exclude_set]
        # If excluding everything would leave too few questions, fall back
        # to the full pool rather than returning a too-short quiz.
        if len(pool) >= (easy + medium + hard):
            all_questions = pool

    buckets: dict[str, list[Question]] = {"easy": [], "medium": [], "hard": []}
    for q in all_questions:
        buckets[_difficulty_tier(q.difficulty)].append(q)

    selected: list[Question] = []
    requested = {"easy": easy, "medium": medium, "hard": hard}
    for tier, count in requested.items():
        pool = buckets[tier]
        selected.extend(random.sample(pool, min(count, len(pool))))

    # Backfill from the overall remaining pool if a tier came up short
    # (e.g. a brand-new subject with few hard questions yet).
    shortfall = (easy + medium + hard) - len(selected)
    if shortfall > 0:
        remaining = [q for q in all_questions if q not in selected]
        selected.extend(random.sample(remaining, min(shortfall, len(remaining))))

    random.shuffle(selected)
    return selected

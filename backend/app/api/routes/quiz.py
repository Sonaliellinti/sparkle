"""Diagnostic quiz — attempt lifecycle skeleton.

Phase 1 scope: create an attempt, list its (unanswered) questions, and
persist raw responses exactly as submitted. Grading beyond a trivial
stored `is_correct` flag, confidence-weighted mastery scoring, and
weakness propagation are all part of the diagnosis engine and are
built in Phase 2 — nothing here computes a diagnosis.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.quiz import AttemptStatus, Question, QuizAttempt, QuizResponse
from app.models.user import User
from app.schemas.quiz import (
    QuestionPublic,
    QuizAttemptRead,
    QuizResponseCreate,
    QuizResponseRead,
)
from app.services import diagnosis_engine, quiz_engine

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.get("/generate", response_model=list[QuestionPublic])
def generate_quiz(
    subject: str | None = None,
    easy: int = 3,
    medium: int = 4,
    hard: int = 3,
    db: Session = Depends(get_db),
):
    """Randomly generates a quiz -- different every call. `subject` is one
    of dsa/python/sql/ml/mixed (default: mixed across all subjects)."""
    return quiz_engine.generate_quiz(db, subject=subject, easy=easy, medium=medium, hard=hard)


@router.get("/attempts", response_model=list[QuizAttemptRead])
def list_attempts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == current_user.id)
        .order_by(QuizAttempt.started_at.desc())
        .all()
    )


@router.post("/attempts", response_model=QuizAttemptRead, status_code=status.HTTP_201_CREATED)
def start_attempt(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = QuizAttempt(user_id=current_user.id, status=AttemptStatus.in_progress)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


@router.get("/questions", response_model=list[QuestionPublic])
def list_questions(db: Session = Depends(get_db)):
    """Returns the question bank without answers. Empty until Phase 2
    seed data is loaded."""
    return db.query(Question).all()


@router.post(
    "/attempts/{attempt_id}/responses",
    response_model=QuizResponseRead,
    status_code=status.HTTP_201_CREATED,
)
def submit_response(
    attempt_id: int,
    payload: QuizResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = db.get(QuizAttempt, attempt_id)
    if attempt is None or attempt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found.")

    question = db.get(Question, payload.question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found.")

    response = QuizResponse(
        attempt_id=attempt_id,
        question_id=payload.question_id,
        selected_option=payload.selected_option,
        # Trivial equality check only — NOT the diagnosis engine.
        is_correct=(payload.selected_option == question.correct_option),
        confidence=payload.confidence,
        reasoning_text=payload.reasoning_text,
        time_taken_seconds=payload.time_taken_seconds,
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    return response


@router.post("/attempts/{attempt_id}/complete", response_model=QuizAttemptRead)
def complete_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime, timezone

    attempt = db.get(QuizAttempt, attempt_id)
    if attempt is None or attempt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found.")

    attempt.status = AttemptStatus.completed
    attempt.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(attempt)

    # Run the deterministic diagnosis engine now that the attempt is complete.
    # This writes ConceptMastery rows + a DiagnosisReport for this attempt.
    diagnosis_engine.run_diagnosis(db, attempt_id)

    return attempt

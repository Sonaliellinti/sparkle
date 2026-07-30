"""Diagnosis report routes — placeholder for Phase 2.

Intentionally NOT implemented yet: the deterministic diagnosis engine
(mastery scoring + NetworkX weakness propagation + roadmap generation)
is the core deliverable of Phase 2. This router exists now so the
route + URL contract is fixed and the frontend can be scaffolded
against it, but it returns 501 until that engine lands.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.diagnosis import DiagnosisReport
from app.models.quiz import QuizAttempt
from app.models.user import User
from app.schemas.diagnosis import DiagnosisReportRead

router = APIRouter(prefix="/diagnosis", tags=["diagnosis"])


@router.get("/attempts/{attempt_id}", response_model=DiagnosisReportRead)
def get_diagnosis_for_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = db.get(QuizAttempt, attempt_id)
    if attempt is None or attempt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found.")

    report = (
        db.query(DiagnosisReport).filter(DiagnosisReport.attempt_id == attempt_id).first()
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=(
                "Diagnosis generation is not implemented yet — "
                "this is built in Phase 2 (mastery scoring + weakness propagation)."
            ),
        )
    return report

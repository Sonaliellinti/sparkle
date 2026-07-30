"""Dashboard aggregate routes — placeholder for Phase 2.

Will aggregate ConceptMastery rows into the chart-ready shape Recharts
needs on the frontend. No aggregation logic yet.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.diagnosis import ConceptMastery
from app.models.user import User
from app.schemas.diagnosis import ConceptMasteryRead

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/mastery", response_model=list[ConceptMasteryRead])
def get_mastery_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns whatever mastery rows currently exist for the student.
    Empty until Phase 2's diagnosis engine populates ConceptMastery."""
    return (
        db.query(ConceptMastery)
        .filter(ConceptMastery.user_id == current_user.id)
        .all()
    )

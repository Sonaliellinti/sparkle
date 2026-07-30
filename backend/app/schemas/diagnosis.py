from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.diagnosis import MasteryLevel


class ConceptMasteryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    concept_id: int
    score: float
    level: MasteryLevel
    is_propagated: bool
    updated_at: datetime


class DiagnosisReportRead(BaseModel):
    """Shape of the diagnosis engine's output — the `summary` field's
    exact contents (weak concepts, roadmap, etc.) are defined and
    populated when the engine is built in Phase 2."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    attempt_id: int
    summary: dict
    generated_at: datetime

"""
Output-side models of the diagnosis engine: per-concept mastery scores
and a per-attempt diagnosis report.

IMPORTANT (Phase 1 scope): these are pure storage tables. The actual
scoring algorithm, NetworkX weakness-propagation, and roadmap generation
are business logic and are intentionally NOT implemented until Phase 2 —
this file only defines where their outputs will live.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MasteryLevel(str, enum.Enum):
    weak = "weak"
    moderate = "moderate"
    strong = "strong"


class ConceptMastery(Base):
    """One row per (user, concept): the current mastery score for that
    concept, recomputed whenever a new diagnosis is generated."""

    __tablename__ = "concept_masteries"
    __table_args__ = (
        UniqueConstraint("user_id", "concept_id", name="uq_user_concept_mastery"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), nullable=False)

    # Deterministic score in [0, 1], produced by the Phase 2 diagnosis engine.
    score: Mapped[float] = mapped_column(Float, default=0.0)
    level: Mapped[MasteryLevel] = mapped_column(Enum(MasteryLevel), default=MasteryLevel.weak)

    # True if this concept's weakness was *inferred* via graph propagation
    # from a related concept rather than directly tested in the quiz.
    is_propagated: Mapped[bool] = mapped_column(default=False)

    # True if accuracy looks fine but confidence/reasoning patterns suggest
    # guessing or a lingering misconception (Phase 4 hidden-weakness detection).
    hidden_risk: Mapped[bool] = mapped_column(default=False)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ───────────────────────────────────────────────────
    user: Mapped["User"] = relationship(back_populates="concept_masteries")
    concept: Mapped["Concept"] = relationship()

    def __repr__(self) -> str:
        return f"<ConceptMastery user_id={self.user_id} concept_id={self.concept_id} score={self.score}>"


class DiagnosisReport(Base):
    """One row per completed quiz attempt: the generated diagnosis snapshot
    (weak concepts, roadmap, etc.) stored as JSON for flexibility while the
    exact shape of the diagnosis output evolves across phases."""

    __tablename__ = "diagnosis_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("quiz_attempts.id"), unique=True, nullable=False
    )

    # Populated by the Phase 2 diagnosis engine, e.g.:
    # {"weak_concepts": [...], "propagated_concepts": [...], "roadmap": [...]}
    summary: Mapped[dict] = mapped_column(JSON, default=dict)

    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # ── Relationships ───────────────────────────────────────────────────
    user: Mapped["User"] = relationship(back_populates="diagnosis_reports")
    attempt: Mapped["QuizAttempt"] = relationship(back_populates="diagnosis_report")

    def __repr__(self) -> str:
        return f"<DiagnosisReport attempt_id={self.attempt_id}>"

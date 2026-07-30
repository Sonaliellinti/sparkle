"""
Diagnostic quiz models: questions, attempts, and per-question responses.

Confidence and free-text reasoning are captured on `QuizResponse` because
the (Phase 2) diagnosis engine treats "wrong but confident" very
differently from "wrong and unsure" when computing mastery, and the
reasoning text is later embedded (sentence-transformers) for
misconception matching in Phase 3. None of that logic lives here —
this file only defines storage.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AttemptStatus(str, enum.Enum):
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id"), nullable=False)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    # Stored as a JSON object, e.g. {"A": "...", "B": "...", "C": "...", "D": "..."}
    # JSON works identically on SQLite and Postgres, so no migration needed later.
    options: Mapped[dict] = mapped_column(JSON, nullable=False)
    correct_option: Mapped[str] = mapped_column(String(4), nullable=False)

    difficulty: Mapped[int] = mapped_column(Integer, default=1)  # 1 (easy) - 5 (hard)

    # Optional additional concepts this question also exercises (list of concept
    # ids), e.g. a Kirchhoff's-law question that also leans on Ohm's law. The
    # diagnosis engine (Phase 4) folds responses into ALL tagged concepts, not
    # just the primary one.
    secondary_concept_ids: Mapped[list] = mapped_column(JSON, default=list)

    # Canonical explanation of the correct approach; shown to the student
    # and also used as grounding context for Groq mistake explanations later.
    explanation: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # ── Relationships ───────────────────────────────────────────────────
    concept: Mapped["Concept"] = relationship(back_populates="questions")
    responses: Mapped[list["QuizResponse"]] = relationship(back_populates="question")

    def __repr__(self) -> str:
        return f"<Question id={self.id} concept_id={self.concept_id}>"


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    status: Mapped[AttemptStatus] = mapped_column(
        Enum(AttemptStatus), default=AttemptStatus.in_progress, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Relationships ───────────────────────────────────────────────────
    user: Mapped["User"] = relationship(back_populates="quiz_attempts")
    responses: Mapped[list["QuizResponse"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )
    diagnosis_report: Mapped["DiagnosisReport | None"] = relationship(
        back_populates="attempt", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<QuizAttempt id={self.id} user_id={self.user_id} status={self.status}>"


class QuizResponse(Base):
    __tablename__ = "quiz_responses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("quiz_attempts.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)

    selected_option: Mapped[str | None] = mapped_column(String(4), nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)

    # Self-reported confidence, 1 (guessing) - 5 (certain). Core input to the
    # deterministic mastery-scoring algorithm built in Phase 2.
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)

    # Optional free-text "why did you choose this?" — embedded via
    # sentence-transformers in Phase 3 for misconception clustering.
    reasoning_text: Mapped[str] = mapped_column(Text, default="", nullable=False)

    time_taken_seconds: Mapped[float] = mapped_column(Float, default=0.0)

    # ── Relationships ───────────────────────────────────────────────────
    attempt: Mapped["QuizAttempt"] = relationship(back_populates="responses")
    question: Mapped["Question"] = relationship(back_populates="responses")

    def __repr__(self) -> str:
        return f"<QuizResponse attempt_id={self.attempt_id} question_id={self.question_id}>"

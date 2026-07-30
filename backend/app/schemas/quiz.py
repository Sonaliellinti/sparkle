from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.quiz import AttemptStatus


class QuestionPublic(BaseModel):
    """Question shape shown to the student — deliberately excludes
    `correct_option` and `explanation` so the quiz can't be cheated by
    inspecting the API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    concept_id: int
    text: str
    options: dict
    difficulty: int


class QuizAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: AttemptStatus
    started_at: datetime
    completed_at: datetime | None = None


class QuizResponseCreate(BaseModel):
    question_id: int
    selected_option: str = Field(max_length=4)
    confidence: int = Field(ge=1, le=5)
    reasoning_text: str = ""
    time_taken_seconds: float = 0.0


class QuizResponseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    selected_option: str | None
    is_correct: bool
    confidence: int
    reasoning_text: str
    time_taken_seconds: float

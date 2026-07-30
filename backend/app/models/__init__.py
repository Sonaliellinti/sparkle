"""
Importing every model module here ensures they all register with
`Base.metadata` — required both for `Base.metadata.create_all()` and for
Alembic's autogenerate to see the full schema.
"""
from app.models.user import User
from app.models.concept import Concept, ConceptDependency
from app.models.quiz import Question, QuizAttempt, QuizResponse, AttemptStatus
from app.models.diagnosis import ConceptMastery, DiagnosisReport, MasteryLevel
from app.models.tutor import TutorMessage

__all__ = [
    "TutorMessage",
    "User",
    "Concept",
    "ConceptDependency",
    "Question",
    "QuizAttempt",
    "QuizResponse",
    "AttemptStatus",
    "ConceptMastery",
    "DiagnosisReport",
    "MasteryLevel",
]

"""
AI-feature routes. This is the ONLY router that touches app.services.groq_service.
Every endpoint here consumes output the diagnosis engine already produced —
none of them re-decide what's weak or what's correct.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.concept import Concept
from app.models.diagnosis import ConceptMastery, DiagnosisReport, MasteryLevel
from app.models.quiz import QuizAttempt, QuizResponse
from app.models.tutor import TutorMessage
from app.models.user import User
from app.services import embedding_service, groq_service

router = APIRouter(prefix="/ai", tags=["ai"])


# ── Mistake explanation ─────────────────────────────────────────────────────
@router.get("/explain-mistake/{response_id}")
def explain_mistake(
    response_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    response = db.get(QuizResponse, response_id)
    if response is None or response.attempt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Response not found.")

    question = response.question
    misconceptions: list[str] = []
    report = (
        db.query(DiagnosisReport)
        .filter(DiagnosisReport.attempt_id == response.attempt_id)
        .first()
    )
    if report:
        for entry in report.summary.get("weak_concepts", []) + report.summary.get("hidden_risks", []):
            if entry["concept_id"] == question.concept_id:
                misconceptions = entry.get("misconceptions", [])
                break

    explanation = groq_service.explain_mistake(
        question_text=question.text,
        selected_option=response.selected_option or "(no answer)",
        correct_option=question.correct_option,
        reference_explanation=question.explanation,
        misconceptions=misconceptions,
    )
    return {"response_id": response_id, "explanation": explanation}


@router.get("/roadmap/subject/{subject}")
def get_subject_roadmap(
    subject: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Per-subject recommendation for the dashboard's subject cards, driven
    by the student's CURRENT ConceptMastery state for that subject (not
    tied to a single attempt) -- so it stays current across multiple
    independent quizzes taken over time."""
    weak_masteries = (
        db.query(ConceptMastery)
        .join(Concept, ConceptMastery.concept_id == Concept.id)
        .filter(
            ConceptMastery.user_id == current_user.id,
            Concept.subject == subject,
            ConceptMastery.level == MasteryLevel.weak,
        )
        .all()
    )
    concept_by_id = {m.concept_id: db.get(Concept, m.concept_id) for m in weak_masteries}
    weak_concepts = [
        {
            "concept_id": m.concept_id,
            "slug": concept_by_id[m.concept_id].slug,
            "name": concept_by_id[m.concept_id].name,
            "score": round(m.score, 3),
            "is_propagated": m.is_propagated,
            "hidden_risk": m.hidden_risk,
            "misconceptions": [],
            "root_cause_concept_id": None,
        }
        for m in weak_masteries
    ]
    roadmap_text = groq_service.generate_roadmap(weak_concepts)
    return {"subject": subject, "weak_concepts": weak_concepts, "roadmap": roadmap_text}


# ── Personalized roadmap ────────────────────────────────────────────────────
@router.get("/roadmap/{attempt_id}")
def get_roadmap(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    attempt = db.get(QuizAttempt, attempt_id)
    if attempt is None or attempt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found.")

    report = db.query(DiagnosisReport).filter(DiagnosisReport.attempt_id == attempt_id).first()
    weak_concepts = report.summary.get("weak_concepts", []) if report else []

    roadmap_text = groq_service.generate_roadmap(weak_concepts)
    return {"attempt_id": attempt_id, "weak_concepts": weak_concepts, "roadmap": roadmap_text}


# ── AI tutor (scope-restricted) ─────────────────────────────────────────────
def _current_weak_concepts(db: Session, user_id: int) -> list[Concept]:
    weak_masteries = (
        db.query(ConceptMastery)
        .filter(ConceptMastery.user_id == user_id, ConceptMastery.level == MasteryLevel.weak)
        .all()
    )
    concept_ids = [m.concept_id for m in weak_masteries]
    if not concept_ids:
        return []
    return db.query(Concept).filter(Concept.id.in_(concept_ids)).all()


REDIRECT_MESSAGE = (
    "That's outside what your latest diagnosis flagged. Let's stick to your current "
    "weak areas for now — check your roadmap on the dashboard, or ask me about one "
    "of those concepts instead."
)
OFF_TOPIC_SIMILARITY_THRESHOLD = 0.15


@router.post("/tutor")
def tutor_chat(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    message = (payload.get("message") or "").strip()
    if not message:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="message is required.")

    weak_concepts = _current_weak_concepts(db, current_user.id)
    weak_names = [c.name for c in weak_concepts]

    if not weak_concepts:
        reply = "Take a diagnostic quiz first — once it's graded, I'll know exactly which concepts to help you with."
    else:
        # Server-side scope enforcement: check the message's similarity against
        # the student's weak concept names/descriptions BEFORE ever calling Groq.
        # This is a hard gate, not just a prompt instruction (see docs/PROJECT_PLAN.md §8).
        best_similarity = max(
            embedding_service.similarity(message, f"{c.name}. {c.description}")
            for c in weak_concepts
        )
        if best_similarity < OFF_TOPIC_SIMILARITY_THRESHOLD:
            reply = REDIRECT_MESSAGE
        else:
            db.add(TutorMessage(user_id=current_user.id, role="user", content=message))
            db.flush()
            history = (
                db.query(TutorMessage)
                .filter(TutorMessage.user_id == current_user.id)
                .order_by(TutorMessage.created_at.asc())
                .all()
            )
            conversation = [{"role": m.role, "content": m.content} for m in history]
            reply = groq_service.tutor_reply(conversation, weak_names)

    db.add(TutorMessage(user_id=current_user.id, role="assistant", content=reply))
    db.commit()
    return {"reply": reply, "weak_concepts": weak_names}


@router.get("/tutor/history")
def tutor_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    history = (
        db.query(TutorMessage)
        .filter(TutorMessage.user_id == current_user.id)
        .order_by(TutorMessage.created_at.asc())
        .all()
    )
    return [{"role": m.role, "content": m.content, "created_at": m.created_at} for m in history]

"""Concept dependency graph — read endpoints.

Phase 1 scope: expose whatever is in the `concepts` /
`concept_dependencies` tables as-is. Seed data (the actual Current
Electricity concept graph) and any graph algorithms (NetworkX
propagation, etc.) are built in Phase 2.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.concept import Concept, ConceptDependency
from app.models.user import User
from app.schemas.concept import ConceptGraphRead, ConceptRead
from app.schemas.quiz import QuestionPublic
from app.services import graph_service

router = APIRouter(prefix="/concepts", tags=["concepts"])


@router.get("", response_model=list[ConceptRead])
def list_concepts(db: Session = Depends(get_db)):
    return db.query(Concept).all()


@router.get("/graph", response_model=ConceptGraphRead)
def get_concept_graph(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns nodes + edges shaped for React Flow. Empty until Phase 2
    seed data is loaded — the endpoint contract is established now so
    the frontend can be built against it immediately."""
    nodes = db.query(Concept).all()
    edges = db.query(ConceptDependency).all()
    return ConceptGraphRead(nodes=nodes, edges=edges)


def _get_concept_or_404(db: Session, concept_id: int) -> Concept:
    concept = db.get(Concept, concept_id)
    if concept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Concept not found.")
    return concept


@router.get("/{concept_id}/prerequisites", response_model=list[ConceptRead])
def get_prerequisites(
    concept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_concept_or_404(db, concept_id)
    graph = graph_service.load_graph(db)
    prereq_ids = graph_service.prerequisites_of(graph, concept_id)
    return db.query(Concept).filter(Concept.id.in_(prereq_ids)).all()


@router.get("/{concept_id}/questions", response_model=list[QuestionPublic])
def get_questions_for_concept(
    concept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_concept_or_404(db, concept_id)
    return graph_service.questions_for_concept(db, concept_id)

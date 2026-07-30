"""
Concept dependency graph service.

This is the ONLY module in the project that imports `networkx` directly.
Every other module (routes, diagnosis engine) goes through the functions
here, so graph algorithms stay in one well-documented place.
"""
import networkx as nx
from sqlalchemy.orm import Session

from app.models.concept import Concept, ConceptDependency
from app.models.quiz import Question


def load_graph(db: Session) -> nx.DiGraph:
    """Builds a directed graph from the `concepts` / `concept_dependencies`
    tables. Cheap to rebuild per-request at this scale (~10 nodes); see
    docs/PROJECT_PLAN.md §3.6 for the caching seam if that ever changes."""
    graph = nx.DiGraph()

    concepts = db.query(Concept).all()
    for c in concepts:
        graph.add_node(c.id, slug=c.slug, name=c.name, difficulty_level=c.difficulty_level)

    edges = db.query(ConceptDependency).all()
    for e in edges:
        graph.add_edge(e.prerequisite_id, e.dependent_id, weight=e.weight)

    return graph


def topological_concept_order(graph: nx.DiGraph) -> list[int]:
    """Returns concept ids in dependency order (prerequisites before
    dependents). The graph is authored as a DAG; this raises
    NetworkXUnfeasible if a cycle is ever introduced by bad seed data,
    which is exactly the kind of authoring bug we want surfaced loudly."""
    return list(nx.topological_sort(graph))


def prerequisites_of(graph: nx.DiGraph, concept_id: int) -> list[int]:
    """Direct prerequisites (immediate predecessors) of a concept."""
    if concept_id not in graph:
        return []
    return list(graph.predecessors(concept_id))


def dependents_of(graph: nx.DiGraph, concept_id: int) -> list[int]:
    """Direct dependents (immediate successors) of a concept."""
    if concept_id not in graph:
        return []
    return list(graph.successors(concept_id))


def questions_for_concept(db: Session, concept_id: int) -> list[Question]:
    """All questions tagged to a concept, either as their primary concept or
    listed in `secondary_concept_ids`."""
    primary = db.query(Question).filter(Question.concept_id == concept_id).all()
    # SQLite/Postgres-portable secondary-tag lookup done in Python rather than
    # a JSON-contains query, since it needs to work identically on both.
    all_questions = db.query(Question).all()
    secondary = [
        q for q in all_questions
        if q.concept_id != concept_id and concept_id in (q.secondary_concept_ids or [])
    ]
    return primary + secondary

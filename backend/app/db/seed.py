"""
Idempotent database seed script.

Run with:
    python -m app.db.seed

Safe to re-run: looks up existing rows by slug/unique keys before inserting,
so it won't create duplicates if run multiple times.
"""
from app.core.database import Base, engine, session_scope
from app.db.concept_graph_data import CONCEPTS, EDGES
from app.db.question_bank import QUESTIONS
from app.models.concept import Concept, ConceptDependency
from app.models.quiz import Question

import app.models  # noqa: F401  (ensures all tables are registered)


def seed_concepts(db) -> dict[str, Concept]:
    slug_to_concept: dict[str, Concept] = {}
    for c in CONCEPTS:
        existing = db.query(Concept).filter(Concept.slug == c["slug"]).first()
        if existing:
            slug_to_concept[c["slug"]] = existing
            continue
        concept = Concept(**c)
        db.add(concept)
        db.flush()
        slug_to_concept[c["slug"]] = concept
    return slug_to_concept


def seed_edges(db, slug_to_concept: dict[str, Concept]) -> None:
    for prereq_slug, dep_slug, weight in EDGES:
        prereq = slug_to_concept[prereq_slug]
        dep = slug_to_concept[dep_slug]
        existing = (
            db.query(ConceptDependency)
            .filter(
                ConceptDependency.prerequisite_id == prereq.id,
                ConceptDependency.dependent_id == dep.id,
            )
            .first()
        )
        if existing:
            continue
        db.add(
            ConceptDependency(
                prerequisite_id=prereq.id,
                dependent_id=dep.id,
                weight=weight,
            )
        )


def seed_questions(db, slug_to_concept: dict[str, Concept]) -> int:
    inserted = 0
    for q in QUESTIONS:
        concept = slug_to_concept[q["concept_slug"]]
        existing = (
            db.query(Question)
            .filter(Question.concept_id == concept.id, Question.text == q["text"])
            .first()
        )
        if existing:
            continue
        db.add(
            Question(
                concept_id=concept.id,
                text=q["text"],
                options=q["options"],
                correct_option=q["correct_option"],
                difficulty=q["difficulty"],
                explanation=q["explanation"],
                secondary_concept_ids=[],
            )
        )
        inserted += 1
    return inserted


def run_seed() -> None:
    Base.metadata.create_all(bind=engine)
    with session_scope() as db:
        slug_to_concept = seed_concepts(db)
        db.flush()
        seed_edges(db, slug_to_concept)
        n_questions = seed_questions(db, slug_to_concept)
        db.flush()
        print(f"Seeded {len(slug_to_concept)} concepts, {len(EDGES)} edges, {n_questions} new questions.")


if __name__ == "__main__":
    run_seed()

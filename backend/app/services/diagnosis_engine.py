"""
Deterministic diagnosis engine.

This module NEVER imports Groq or any LLM client. Every score, label, and
propagation decision here is plain, reproducible Python + graph math, so
the same quiz responses always produce the same diagnosis. The LLM layer
(app/services/groq_service.py) only explains or narrates what this module
has already decided — it cannot change a mastery score or a weak/strong
label.
"""
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.concept import Concept
from app.models.diagnosis import ConceptMastery, DiagnosisReport, MasteryLevel
from app.models.quiz import QuizAttempt, QuizResponse
from app.services import embedding_service, graph_service
from app.db.concept_graph_data import MISCONCEPTIONS

# ── Tunable thresholds (kept as named constants, not magic numbers) ───────
WEAK_THRESHOLD = 0.5
STRONG_THRESHOLD = 0.8
OVERCONFIDENT_MISS_PENALTY = 1.4   # extra weight for wrong-but-confident answers
LOW_CONFIDENCE_MISS_PENALTY = 0.8  # reduced weight for wrong-but-unsure answers
GUESS_ACCURACY_FLOOR = 0.6         # "hidden risk": high accuracy but low avg confidence
GUESS_CONFIDENCE_CEILING = 2.5
MISCONCEPTION_MATCH_THRESHOLD = 0.55


@dataclass
class ConceptSignal:
    """Intermediate per-concept aggregation used while scoring."""
    concept_id: int
    responses: list[QuizResponse] = field(default_factory=list)
    misconception_hits: list[str] = field(default_factory=list)


def _confidence_weight(is_correct: bool, confidence: int) -> float:
    """Per-response weight applied when averaging into a mastery score.
    See docs/PROJECT_PLAN.md §4.2 for the calibration table this encodes."""
    if is_correct:
        return 1.0
    if confidence >= 4:
        return OVERCONFIDENT_MISS_PENALTY  # overconfident miss = strongest weakness signal
    return LOW_CONFIDENCE_MISS_PENALTY


def _mastery_level(score: float) -> MasteryLevel:
    if score >= STRONG_THRESHOLD:
        return MasteryLevel.strong
    if score >= WEAK_THRESHOLD:
        return MasteryLevel.moderate
    return MasteryLevel.weak


def _compute_direct_mastery(signal: ConceptSignal) -> float:
    """Confidence-weighted accuracy for a directly-tested concept, in [0, 1]."""
    if not signal.responses:
        return 0.0

    total_weight = 0.0
    earned_weight = 0.0
    for r in signal.responses:
        w = _confidence_weight(r.is_correct, r.confidence)
        total_weight += w
        if r.is_correct:
            earned_weight += w
    if total_weight == 0:
        return 0.0
    return max(0.0, min(1.0, earned_weight / total_weight))


def _detect_hidden_risk(signal: ConceptSignal, direct_score: float) -> bool:
    """A concept can score as 'mastered' on raw accuracy while still hiding
    a problem: consistently low confidence despite correct answers (guessing),
    or reasoning text repeatedly matching a known misconception even when the
    final answer was right."""
    if not signal.responses:
        return False

    accuracy = sum(1 for r in signal.responses if r.is_correct) / len(signal.responses)
    avg_confidence = sum(r.confidence for r in signal.responses) / len(signal.responses)

    guessing_pattern = accuracy >= GUESS_ACCURACY_FLOOR and avg_confidence <= GUESS_CONFIDENCE_CEILING
    lingering_misconception = len(signal.misconception_hits) > 0 and direct_score >= WEAK_THRESHOLD

    return guessing_pattern or lingering_misconception


def _collect_misconception_hits(signal: ConceptSignal, concept_slug: str) -> list[str]:
    known = MISCONCEPTIONS.get(concept_slug, [])
    if not known:
        return []
    hits: list[str] = []
    for r in signal.responses:
        matches = embedding_service.misconception_similarity(
            r.reasoning_text, known, threshold=MISCONCEPTION_MATCH_THRESHOLD
        )
        hits.extend(label for label, _score in matches)
    return list(dict.fromkeys(hits))  # de-dup, preserve order


def _propagate_weakness(
    graph, direct_scores: dict[int, float], tested_concept_ids: set[int]
) -> dict[int, tuple[float, bool]]:
    """Forward-propagates weakness from weak prerequisites to untested
    dependents, per docs/PROJECT_PLAN.md §3.5. Returns
    {concept_id: (score, is_propagated)} for every node in the graph."""
    scores: dict[int, tuple[float, bool]] = {
        cid: (direct_scores.get(cid, 1.0), False) for cid in graph.nodes
    }
    # Concepts never tested default to a neutral 1.0 (no evidence either way)
    # unless propagation from a weak prerequisite pulls them down below.
    for cid in graph.nodes:
        if cid not in tested_concept_ids:
            scores[cid] = (1.0, False)

    for concept_id in graph_service.topological_concept_order(graph):
        if concept_id in tested_concept_ids:
            continue  # never overwrite a directly-measured score
        current_score, _ = scores[concept_id]
        penalty = 0.0
        propagated = False
        for prereq_id in graph.predecessors(concept_id):
            prereq_score, _ = scores[prereq_id]
            if prereq_score < WEAK_THRESHOLD:
                weight = graph.edges[prereq_id, concept_id]["weight"]
                penalty += weight * (WEAK_THRESHOLD - prereq_score)
                propagated = True
        if propagated:
            new_score = max(0.0, min(1.0, current_score - penalty))
            scores[concept_id] = (new_score, True)

    return scores


def _identify_root_causes(
    graph, weak_concept_ids: set[int], final_scores: dict[int, float]
) -> dict[int, int | None]:
    """For each weak concept, checks whether a prerequisite scores
    meaningfully lower — if so, that prerequisite (not the concept itself)
    is the likely root cause to study first."""
    root_causes: dict[int, int | None] = {}
    for concept_id in weak_concept_ids:
        weakest_prereq = None
        weakest_score = final_scores.get(concept_id, 0.0)
        for prereq_id in graph.predecessors(concept_id):
            prereq_score = final_scores.get(prereq_id, 1.0)
            if prereq_score < weakest_score:
                weakest_score = prereq_score
                weakest_prereq = prereq_id
        root_causes[concept_id] = weakest_prereq  # None means the concept is its own root cause
    return root_causes


def run_diagnosis(db: Session, attempt_id: int) -> DiagnosisReport:
    """Orchestrates the full deterministic diagnosis pipeline for one
    completed quiz attempt. Writes/updates ConceptMastery rows and a
    DiagnosisReport, and returns the report."""
    attempt = db.get(QuizAttempt, attempt_id)
    if attempt is None:
        raise ValueError(f"Quiz attempt {attempt_id} not found.")

    responses = (
        db.query(QuizResponse).filter(QuizResponse.attempt_id == attempt_id).all()
    )

    concepts = {c.id: c for c in db.query(Concept).all()}
    graph = graph_service.load_graph(db)

    # ── 1. Group responses by every concept they're tagged to ───────────
    signals: dict[int, ConceptSignal] = {}
    for r in responses:
        question = r.question
        tagged_ids = [question.concept_id, *(question.secondary_concept_ids or [])]
        for cid in tagged_ids:
            signals.setdefault(cid, ConceptSignal(concept_id=cid)).responses.append(r)

    # ── 2. Direct mastery + misconception matching per tested concept ───
    direct_scores: dict[int, float] = {}
    for cid, signal in signals.items():
        concept_slug = concepts[cid].slug if cid in concepts else ""
        signal.misconception_hits = _collect_misconception_hits(signal, concept_slug)
        direct_scores[cid] = _compute_direct_mastery(signal)

    tested_ids = set(signals.keys())

    # ── 2b. Restrict this run to the subject(s) actually touched ────────
    # Sparkle supports independent per-subject quizzes (DSA / Python / SQL /
    # ML). Since the concept graph doesn't have cross-subject edges, we
    # scope both propagation and persistence to only the touched subjects'
    # nodes -- otherwise every quiz completion would reset ConceptMastery
    # for the OTHER three subjects back to a neutral baseline, destroying
    # their independently-tracked progress.
    touched_subjects = {concepts[cid].subject for cid in tested_ids if cid in concepts}
    relevant_node_ids = {
        cid for cid, c in concepts.items() if c.subject in touched_subjects
    }
    graph = graph.subgraph(relevant_node_ids)

    # ── 3. Propagate weakness through the graph to untested concepts ────
    propagated_scores = _propagate_weakness(graph, direct_scores, tested_ids)

    # ── 4. Hidden-risk detection (only meaningful for tested concepts) ───
    hidden_risk_ids = {
        cid for cid, signal in signals.items()
        if _detect_hidden_risk(signal, direct_scores[cid])
    }

    # ── 5. Persist ConceptMastery rows ───────────────────────────────────
    final_scores: dict[int, float] = {}
    for cid, (score, is_propagated) in propagated_scores.items():
        final_scores[cid] = score
        level = _mastery_level(score)
        mastery = (
            db.query(ConceptMastery)
            .filter(ConceptMastery.user_id == attempt.user_id, ConceptMastery.concept_id == cid)
            .first()
        )
        if mastery is None:
            mastery = ConceptMastery(user_id=attempt.user_id, concept_id=cid)
            db.add(mastery)
        mastery.score = score
        mastery.level = level
        mastery.is_propagated = is_propagated
        mastery.hidden_risk = cid in hidden_risk_ids

    db.flush()

    # ── 6. Root cause identification for weak concepts ───────────────────
    weak_ids = {cid for cid, score in final_scores.items() if score < WEAK_THRESHOLD}
    root_causes = _identify_root_causes(graph, weak_ids, final_scores)

    def _concept_summary(cid: int) -> dict:
        c = concepts.get(cid)
        return {
            "concept_id": cid,
            "slug": c.slug if c else None,
            "name": c.name if c else None,
            "score": round(final_scores.get(cid, 0.0), 3),
            "is_propagated": propagated_scores[cid][1],
            "hidden_risk": cid in hidden_risk_ids,
            "misconceptions": signals[cid].misconception_hits if cid in signals else [],
            "root_cause_concept_id": root_causes.get(cid),
        }

    summary = {
        "weak_concepts": [_concept_summary(cid) for cid in sorted(weak_ids)],
        "hidden_risks": [_concept_summary(cid) for cid in sorted(hidden_risk_ids)],
        "all_scores": {cid: round(score, 3) for cid, score in final_scores.items()},
    }

    report = (
        db.query(DiagnosisReport).filter(DiagnosisReport.attempt_id == attempt_id).first()
    )
    if report is None:
        report = DiagnosisReport(user_id=attempt.user_id, attempt_id=attempt_id, summary=summary)
        db.add(report)
    else:
        report.summary = summary

    db.commit()
    db.refresh(report)
    return report

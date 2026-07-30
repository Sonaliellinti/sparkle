# JEE Learning Diagnosis Platform — Technical Specification (Phases 2–10)

**Scope:** Current Electricity (JEE Main Physics)
**Status:** Phase 1 (project skeleton, auth, DB schema) complete and verified locally.
This document is the build spec for every remaining phase. Each phase will still be
implemented, explained, and approved one at a time in that order — this document is
the shared blueprint, not a signal to build everything at once.

---

## 0. Architecture Recap

```
Next.js 15 (TS, Tailwind, shadcn/ui, React Flow, Recharts)
        │  REST (fetch) + JWT bearer
        ▼
FastAPI  ──►  Deterministic Diagnosis Engine (NetworkX + sentence-transformers)
        │                                   │
        ▼                                   ▼
SQLAlchemy ORM  ──►  SQLite (dev) / Postgres-Supabase (prod)     Groq API (explanations,
                                                                   roadmap, tutor — never
                                                                   grading/diagnosis)
```

Guiding rule carried through every phase below: **anything that decides a score, a
mastery level, or a weak/strong label is deterministic Python/graph code. Groq is only
ever called after that decision is made**, to explain it or talk about it.

---

## Phase 2 — Quiz Module

### 2.1 Data model additions
`Question` and `QuizResponse` already exist from Phase 1 (`app/models/quiz.py`). No new
tables — Phase 2 fills them in properly and adds the CRUD/seed layer:

| Field on `Question` | Purpose |
|---|---|
| `concept_id` | primary concept tag (FK, already present) |
| `secondary_concept_ids` *(new, JSON list)* | for questions that span 2 concepts (e.g. a Kirchhoff's-law question that also needs Ohm's law) |
| `difficulty` | 1–5, already present |
| `options` / `correct_option` / `explanation` | already present |

### 2.2 Question CRUD (admin-facing, minimal)
`app/api/routes/questions_admin.py`:
- `POST /api/v1/admin/questions` — create
- `GET /api/v1/admin/questions` — list/filter by concept, difficulty
- `PUT /api/v1/admin/questions/{id}` — update
- `DELETE /api/v1/admin/questions/{id}` — delete

(No auth-role system exists yet — Phase 2 keeps this behind the same student JWT for
demo purposes; a real "admin" role is a nice-to-have, not required for the hackathon
demo.)

### 2.3 Quiz API (student-facing) — extends Phase 1's skeleton
- `POST /quiz/attempts` — already exists (start attempt)
- `GET /quiz/questions?concept_id=&limit=` — extend to support fetching a randomized
  diagnostic set (e.g. 20 questions spanning all concepts, weighted by difficulty)
- `POST /quiz/attempts/{id}/responses` — already exists; this phase makes
  `is_correct` real (already trivial-equality) and adds the confidence + reasoning
  capture (already in schema) actually rendered/collected by the frontend
- `POST /quiz/attempts/{id}/complete` — already exists; Phase 2 leaves the diagnosis
  hook as a TODO (wired in Phase 4)

### 2.4 Seed data — Current Electricity question bank
Target: **50 questions** across these concept tags (also the Phase 3 graph nodes):

1. `ohms-law` — Ohm's Law & resistance basics
2. `resistivity-temp` — Resistivity, temperature dependence
3. `series-parallel` — Series & parallel combinations
4. `cells-emf` — Cells, EMF, internal resistance
5. `kirchhoff-current` — Kirchhoff's Current Law
6. `kirchhoff-voltage` — Kirchhoff's Voltage Law
7. `wheatstone-bridge` — Wheatstone bridge & meter bridge
8. `potentiometer` — Potentiometer
9. `power-heating` — Electrical power & heating effects
10. `rc-circuits` — RC circuits / charging-discharging

~5 questions per concept, spanning difficulty 1–5, each with: MCQ text, 4 options,
correct option, concept tag(s), difficulty, reference explanation, and the
`reasoning_text` field left for the student to fill in (not pre-seeded — it's
student input).

Seed script: `backend/app/db/seed.py`, run via `python -m app.db.seed`. Idempotent
(checks for existing slugs before inserting) so it's safe to re-run.

### 2.5 Frontend — Quiz interface
`frontend/src/app/quiz/page.tsx` + components in `frontend/src/components/quiz/`:
- `QuizStart.tsx` — start-attempt screen
- `QuestionCard.tsx` — MCQ options + confidence slider (1–5) + optional reasoning
  textarea, one question at a time
- `QuizProgress.tsx` — progress bar / question counter
- `QuizSummary.tsx` — immediate raw score on submit (correctness only — no diagnosis
  yet, that's Phase 4's dashboard)

State: React state + a thin `lib/api/quiz.ts` client wrapping `fetch` with the JWT
from an auth context (`lib/auth-context.tsx`, built alongside this phase since login
UI is also needed here for the first time).

**Definition of done for Phase 2:** a student can log in, start a quiz, answer ~10–20
seeded questions with confidence + optional reasoning, submit, and see a raw score —
fully working end to end, no mocked data.

---

## Phase 3 — Knowledge Graph

### 3.1 Concept graph definition (Current Electricity)
Nodes = the 10 concept slugs above. Edges (`prerequisite → dependent`), each with a
weight in `[0,1]` representing propagation strength:

```
ohms-law            → series-parallel        (0.9)
ohms-law            → resistivity-temp        (0.7)
ohms-law            → power-heating           (0.8)
series-parallel     → wheatstone-bridge        (0.8)
series-parallel     → kirchhoff-current        (0.6)
cells-emf           → kirchhoff-voltage        (0.8)
kirchhoff-current    → kirchhoff-voltage        (0.5)
kirchhoff-voltage    → wheatstone-bridge        (0.6)
cells-emf           → potentiometer            (0.9)
kirchhoff-voltage    → potentiometer            (0.5)
ohms-law            → rc-circuits              (0.6)
power-heating        → rc-circuits              (0.4)
```

This is seeded alongside the questions in `backend/app/db/seed.py` (populates
`Concept` + `ConceptDependency`, already modeled in Phase 1).

### 3.2 Graph service (NetworkX)
New module: `backend/app/services/graph_service.py`
- `load_graph(db) -> nx.DiGraph` — builds an in-memory `DiGraph` from
  `Concept`/`ConceptDependency` rows each request (10 nodes — trivial cost; no need
  for a persistent graph cache at this scale, but the function is written so a
  cache layer can be dropped in later without changing callers)
- Node attributes: `name`, `difficulty_level`
- Edge attributes: `weight`

This is the **only** place NetworkX is imported — graph algorithms never leak into
API routes or the diagnosis engine's scoring math directly; they're called through
this service.

### 3.3 Question-to-concept mapping
Already modeled via `Question.concept_id` (+ `secondary_concept_ids` from Phase 2).
`graph_service.py` exposes `questions_for_concept(db, concept_id)` used by the
diagnosis engine and by the concept-graph UI's "linked questions" panel (Phase 7).

### 3.4 Concept confidence & mastery score — where they live
- **Concept confidence**: derived per-attempt from the student's self-reported
  `confidence` field on each `QuizResponse`, averaged per concept. Computed in
  Phase 4 (diagnosis engine), stored nowhere new — it's an input signal, not a
  persisted field.
- **Mastery score**: the `ConceptMastery.score` field (already modeled, Phase 1).
  Phase 4 computes and writes it; Phase 3 only prepares the graph the propagation
  step needs.

### 3.5 Prerequisite propagation logic (spec, implemented in Phase 4)
Given directly-measured mastery `m(c)` for tested concepts:
1. For every edge `p → d` with weight `w`, if `m(p)` is weak (below threshold,
   e.g. `< 0.5`) and `d` was **not** directly tested, propagate a discounted penalty
   forward: `m(d) = m(d) - w * (0.5 - m(p))`, clamped to `[0, 1]`.
2. Also propagate **backward**: if a dependent concept `d` is weak but its
   prerequisite `p` scored fine, flag `p` for review at lower confidence (a
   dependent failure with a strong prerequisite usually points at the
   *dependent's own* misconception, not the prerequisite — this asymmetry is what
   "root cause identification" in Phase 4 uses).
3. Concepts touched only via propagation are marked `is_propagated=True` on
   `ConceptMastery` (already modeled) so the UI can visually distinguish
   "we measured this is weak" from "we inferred this might be weak."

Implemented with plain `networkx` traversal (topological order via
`nx.topological_sort`, since the graph is a DAG) — no custom graph library needed.

### 3.6 Storage efficiency
The graph itself (10 nodes, ~12 edges) is cheap enough to rebuild from the two
existing tables on every request — no denormalized graph blob is stored. If the
concept count grows significantly later, `graph_service.load_graph` is the single
seam where an in-memory cache (e.g. rebuilt only when `ConceptDependency` changes)
would be added, without touching any caller.

### 3.7 APIs
Extends Phase 1's `concepts.py` router (already has `/concepts` and
`/concepts/graph` stubs — Phase 3 fills them with real seeded data, no contract
change) and adds:
- `GET /concepts/{id}/questions` — questions tagged to a concept
- `GET /concepts/{id}/prerequisites` — direct prerequisite concepts (for the
  Phase 7 node-click panel)

**Definition of done for Phase 3:** `/concepts/graph` returns the real 10-node,
12-edge Current Electricity graph, ready to render in React Flow.

---

## Phase 4 — Diagnosis Engine

New module: `backend/app/services/diagnosis_engine.py` — the deterministic core.
Explicitly documented as **LLM-free**; Groq is never imported here.

### 4.1 MCQ grading
Already trivial (`selected_option == correct_option`) from Phase 1/2 — Phase 4
consumes this stored `is_correct` rather than re-deriving it.

### 4.2 Confidence scoring
For each response, define a **calibration signal**:
| Correct? | Confidence | Signal |
|---|---|---|
| ✅ | high (4–5) | well-calibrated strength |
| ✅ | low (1–2) | lucky guess — weak signal of real mastery |
| ❌ | high (4–5) | **overconfident miss** — strongest weakness signal |
| ❌ | low (1–2) | honest uncertainty — normal weakness signal |

This produces a per-response weight used in the mastery formula below (e.g.
overconfident misses subtract more from mastery than low-confidence misses).

### 4.3 Sentence-transformers integration (reasoning-text analysis)
`backend/app/services/embedding_service.py`:
- Loads `all-MiniLM-L6-v2` once at module import (singleton), CPU inference.
- `embed(text: str) -> np.ndarray`
- For each concept, a small curated set of **known misconception phrasings** is
  seeded (e.g. for `series-parallel`: "current is the same in parallel branches").
- `misconception_similarity(reasoning_text, concept_id) -> list[(label, score)]`
  computes cosine similarity between the student's reasoning and each known
  misconception embedding for that concept.
- **Not used for grading** — purely descriptive: surfaces *which* misconception a
  wrong (or even right-but-shaky) answer's reasoning resembles, feeding the
  Groq explanation prompt in Phase 5 and the "root cause" label in 4.5.

### 4.4 Hidden weakness detection
A concept can look "mastered" by raw accuracy but hide a problem when:
- accuracy is high but confidence is consistently low (guessing pattern), or
- reasoning-text similarity repeatedly matches a misconception phrasing even on
  questions answered correctly.
Both signals are computed here and folded into a `hidden_risk` flag per concept,
separate from the main `score`/`level`, surfaced on the dashboard as "shaky, worth
reviewing" even when technically "mastered."

### 4.5 Concept mastery score & root cause identification
`compute_mastery(responses_for_concept) -> float in [0,1]`, roughly:
```
score = weighted_accuracy(responses, confidence_weights_from_4.2)
```
then Phase 3's propagation step adjusts scores for untested concepts, and
`identify_root_cause(concept_id, graph)`:
- Looks at the concept's prerequisites in the graph; if a prerequisite scores
  meaningfully lower than the concept itself, the prerequisite is surfaced as the
  likely root cause rather than the concept itself — this is what makes the
  roadmap (Phase 5) point students at the *actual* place to start studying.

### 4.6 Weakness propagation
Implements the algorithm specified in §3.5, using `graph_service.load_graph`.

### 4.7 Orchestration
`run_diagnosis(db, attempt_id) -> DiagnosisReport`:
1. Pull all `QuizResponse` rows for the attempt.
2. Grade + confidence-score + embed reasoning per response.
3. Compute direct mastery per tested concept.
4. Propagate through the graph for untested concepts.
5. Identify root causes for each weak concept.
6. Write/update `ConceptMastery` rows and one `DiagnosisReport.summary` JSON blob:
   `{"weak_concepts": [...], "hidden_risks": [...], "root_causes": {...}}`.
7. Hooked into `POST /quiz/attempts/{id}/complete` from Phase 2 (previously a TODO).

**Definition of done for Phase 4:** completing a quiz produces a real, saved
diagnosis — deterministic, reproducible, no network calls.

---

## Phase 5 — AI Features (Groq)

New module: `backend/app/services/groq_service.py`. Single choke point for every
LLM call in the app.

### 5.1 Mock-first design
```python
def get_groq_client():
    if not settings.GROQ_API_KEY:
        return None  # triggers mock path everywhere below

def explain_mistake(question, response, misconception_labels) -> str:
    client = get_groq_client()
    if client is None:
        return _mock_explanation(question, response)  # realistic canned text
    ...
```
Every public function in this module follows the same try/mock pattern, and every
call is wrapped in `try/except` so a Groq outage or missing key **never** crashes a
request — it silently degrades to mock content. This is the one place `GROQ_API_KEY`
is read.

### 5.2 Endpoints
`backend/app/api/routes/ai.py`:
- `POST /ai/explain-mistake` — input: response id → output: natural-language
  explanation grounded in the question's reference explanation + any detected
  misconception label from 4.3
- `GET /ai/roadmap/{attempt_id}` — input: the diagnosis report's weak/root-cause
  concepts → output: an ordered, personalized study plan (Groq call; deterministic
  ordering of *which* concepts to include comes from the diagnosis engine, Groq
  only writes the explanatory prose/sequencing rationale)
- Tutor endpoint specified in Phase 8

### 5.3 Prompting rules (enforced in code, not just prompt text)
- The prompt always includes only the concepts the diagnosis engine flagged as
  weak/root-cause — Groq is never given the full syllabus to freelance over.
  Same restriction pattern used again in Phase 8's tutor.

**Definition of done for Phase 5:** with no `GROQ_API_KEY` set, explanations and
roadmap read as complete, plausible content (not "N/A" placeholders); with a real
key, real Groq output appears in the same UI with zero frontend changes.

---

## Phase 6 — Dashboard

`frontend/src/app/dashboard/page.tsx`, shadcn/ui + Recharts:
- **Overall score card** — raw quiz accuracy
- **Mastery percentage** — average `ConceptMastery.score` across all concepts
- **Weak concepts list** — from the latest `DiagnosisReport`, with `hidden_risk`
  flags called out distinctly
- **Progress cards** — per-concept mini cards (mastery %, mastered/needs-review/weak
  badge)
- **Recent quizzes** — attempt history table
- **Personalized roadmap** — rendered from Phase 5's `/ai/roadmap` endpoint
- Charts: Recharts `RadarChart` (mastery across all 10 concepts) + `BarChart`
  (accuracy by difficulty)

All data-fetching goes through a `lib/api/dashboard.ts` client; loading and empty
states (no quiz taken yet) designed here, refined in Phase 9.

---

## Phase 7 — Concept Graph UI

`frontend/src/components/graph/ConceptGraph.tsx` (React Flow):
- Custom node component colored by `ConceptMastery.level`:
  🟢 `strong` / 🟡 `moderate` / 🔴 `weak` (and a subtle dashed border for
  `is_propagated=True` nodes — "inferred," not directly tested)
- Edges rendered from `/concepts/graph`, directionality shown with arrowheads
- **Node click → side panel** showing: mastery score, direct prerequisites (from
  `/concepts/{id}/prerequisites`), linked questions (`/concepts/{id}/questions`),
  and static learning-resource links per concept (seeded alongside questions)
- **Post-submission animation**: after a quiz completes, nodes whose mastery
  changed re-color with a brief transition (React Flow node `style` transition +
  a toast summarizing what changed) rather than a hard page reload

---

## Phase 8 — AI Tutor

`frontend/src/app/tutor/page.tsx` + `backend/app/api/routes/ai.py` addition:
`POST /ai/tutor` — request: `{message, conversation_id}` → response: assistant
message.

- **Scope restriction (enforced server-side, not just prompted)**: before calling
  Groq, the backend checks the message's embedding similarity (reusing
  `embedding_service`) against the student's current weak-concept set; if the
  question is clearly about an unrelated concept, the backend **short-circuits**
  with a fixed redirect message pointing back at the roadmap, without calling
  Groq at all. Only in-scope questions reach the LLM, and the system prompt sent
  to Groq also restates the allowed concept list as a hard instruction — two
  layers, not one.
- **Conversation history**: a lightweight `TutorMessage` table (new in this
  phase: `id, user_id, role, content, created_at`) so history persists across
  page reloads; sent back to Groq as context on each turn (bounded to the last
  ~10 turns to control token usage).
- Frontend: simple chat UI (message list + input), shadcn `ScrollArea` +
  `Textarea`, streaming not required for the demo (single request/response is
  fine).

---

## Phase 9 — Polish

Checklist applied across the whole frontend, not a new feature set:
- Consistent spacing/typography scale, shared `Card`/`Badge`/`Button` usage from
  shadcn across dashboard, quiz, graph, tutor
- Loading states: skeleton components for dashboard cards, graph, and quiz
  question fetch
- Error states: toast + inline retry for failed API calls (network errors,
  expired JWT → redirect to login)
- Empty states: "take your first quiz" prompt on an empty dashboard, "no
  messages yet" on tutor
- Mobile responsiveness: quiz and dashboard reflow to single-column below `md`;
  graph gets a "rotate/zoom to explore" hint on small screens
- Subtle motion (Tailwind transitions / Framer-style utility classes) on card
  reveals and node recoloring — nothing that delays interaction

---

## Phase 10 — Deployment

### 10.1 Environment variables (production)
Backend (`.env` on host, never committed):
```
DATABASE_URL=postgresql+psycopg2://...        # Supabase connection string
SECRET_KEY=<strong random value>
GROQ_API_KEY=<real key>
FRONTEND_ORIGIN=https://<vercel-domain>
ENVIRONMENT=production
```
Frontend (Vercel project env):
```
NEXT_PUBLIC_API_BASE_URL=https://<render-or-railway-domain>/api/v1
```

### 10.2 Production settings
- `alembic upgrade head` run as a release step (not `create_all`) — Phase 1's
  dev-only auto-create is disabled when `ENVIRONMENT=production`.
- CORS locked to the real `FRONTEND_ORIGIN` only.
- `sentence-transformers` model cached in the deployment image (avoid a cold
  download on every boot).

### 10.3 Frontend deployment — Vercel
Standard `next build`; connect the GitHub repo, set the one env var above, done —
no server config needed since it's a static/edge Next.js app calling the FastAPI
backend directly.

### 10.4 Backend deployment — Railway or Render
`Dockerfile` (added this phase) running `uvicorn app.main:app --host 0.0.0.0 --port
$PORT`; both platforms auto-detect it. Migration step (`alembic upgrade head`) runs
as a pre-deploy/release command. Database: Supabase Postgres, connection string
dropped into `DATABASE_URL` — no code changes required anywhere, per the
single-seam design from Phase 1.

### 10.5 README structure (generated this phase)
```
1. Overview & architecture diagram
2. Tech stack
3. Local setup — backend (venv, requirements, .env, alembic upgrade, uvicorn)
4. Local setup — frontend (npm install, .env.local, npm run dev)
5. Seeding data (python -m app.db.seed)
6. Running with/without a Groq API key
7. Deployment — Vercel (frontend) + Railway/Render (backend) + Supabase (DB)
8. Project structure reference
9. API reference (link to /docs — FastAPI's auto Swagger UI)
```

---

## Build Order Confirmation

Phases will be implemented in this exact order, each ending in a working,
demoable state before the next starts:

**Phase 2** (quiz + seed data + quiz UI) → **Phase 3** (graph) → **Phase 4**
(diagnosis engine) → **Phase 5** (Groq) → **Phase 6** (dashboard) → **Phase 7**
(graph UI) → **Phase 8** (tutor) → **Phase 9** (polish) → **Phase 10**
(deployment).

Ready to start Phase 2 on your go-ahead.

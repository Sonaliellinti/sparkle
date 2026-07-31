# Sparkle — AI-Powered Interview Readiness Platform

**Diagnose skills. Practice smarter. Get interview ready.**

Sparkle helps students get interview-ready across **DSA, Python, SQL, and
Machine Learning**. Students take randomized quizzes; a **deterministic**
engine grades them, traces weaknesses through a per-subject skill
dependency graph using NetworkX, and produces a personalized study
roadmap. An LLM (Groq) is used **only** to explain mistakes, write the
roadmap's prose, and power an AI mentor that's hard-restricted to the
student's actual weak concepts — it never grades or diagnoses anything
itself.



## 1. Architecture

```
Next.js 15 (TS, Tailwind, hand-built shadcn-style UI, React Flow, Recharts)
        │  REST (fetch) + JWT bearer
        ▼
FastAPI  ──►  Deterministic Diagnosis Engine (NetworkX + sentence-transformers)
        │                                   │
        ▼                                   ▼
SQLAlchemy ORM  ──►  SQLite (dev) / Postgres·Supabase (prod)     Groq API (explanations,
                                                                   roadmap, mentor — never
                                                                   grading/diagnosis)
```

**Guiding rule:** anything that decides a score, a mastery level, or a
weak/strong label is deterministic Python + graph code
(`app/services/diagnosis_engine.py`, `app/services/graph_service.py`,
`app/services/quiz_engine.py`). Groq (`app/services/groq_service.py`) is
only ever called *after* that decision is made, to talk about it — and
every Groq call has a mock fallback, so the app runs fully offline with
`GROQ_API_KEY` unset.

**Independent per-subject tracking:** the four subjects (DSA/Python/SQL/ML)
share one FastAPI backend and one `concepts` graph table, but the
diagnosis engine scopes both weakness-propagation and mastery persistence
to only the subject(s) actually touched by a given quiz attempt — taking
a DSA quiz never resets your SQL/Python/ML progress.

## 2. Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind CSS v4, hand-built shadcn-style components, React Flow, Recharts |
| Backend | FastAPI, SQLAlchemy 2.0, Alembic |
| Database | SQLite locally, Postgres/Supabase in production (one env var swap) |
| AI | sentence-transformers (`all-MiniLM-L6-v2`), NetworkX, Groq API |
| Auth | JWT (python-jose) + bcrypt password hashing |

## 3. Subjects & dynamic quiz engine

Four subjects, each an independent module on the dashboard:

- **DSA** — Arrays, Strings, Hashing, Two Pointers, Sliding Window, Stack, Queue, Linked List, Trees, Graphs, Dynamic Programming
- **Python** — Syntax, Functions, OOP, File Handling, Exceptions, Modules, Standard Library, Problem Solving
- **SQL** — SELECT, WHERE, GROUP BY, ORDER BY, JOINs, Subqueries, Aggregations, Window Functions, Normalization, Indexing
- **Machine Learning** — Linear/Logistic Regression, Classification, Model Evaluation, Precision/Recall, Preprocessing, Feature Engineering, Train/Test Split, Overfitting

Quizzes are **generated on demand**, not fixed: `GET /api/v1/quiz/generate?subject=dsa`
randomly samples a fresh Easy/Medium/Hard mix (default 3/4/3) from the
question bank every time — no two attempts are guaranteed to look alike.
Adding more questions is a pure content change: append entries to
`backend/app/db/question_bank.py` and re-run the seed script — no
application code changes needed.

> **Current content status:** the seeded bank has ~2 questions per concept
> (78 total) to exercise the full engine end-to-end. The product target is
> ~280 questions (100 DSA / 60 Python / 60 SQL / 60 ML) — scaling up the
> bank is a content-writing pass, not an engineering one.

## 4. Project structure

```
jee-diagnosis/
├── backend/
│   ├── app/
│   │   ├── core/            # config, database, security
│   │   ├── models/          # users, concepts (+ subject), quiz, diagnosis, tutor
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── api/routes/      # auth, concepts, quiz, diagnosis, dashboard, ai
│   │   ├── services/        # graph_service, quiz_engine, diagnosis_engine, embedding_service, groq_service
│   │   ├── db/               # concept_graph_data.py, question_bank.py, seed.py
│   │   └── main.py
│   ├── alembic/              # migrations
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/              # /, /login, /register, /quiz, /dashboard, /graph, /tutor
│   │   ├── components/       # ui/ (shadcn-style primitives), quiz/, dashboard/, graph/, layout/
│   │   └── lib/               # api client, auth context
│   ├── Dockerfile
│   └── .env.local.example
├── docs/PROJECT_PLAN.md      # original technical spec
├── render.yaml                # Render Blueprint (backend)
├── docker-compose.yml         # optional one-command local full stack
└── README.md                  # this file
```

## 5. Local setup — backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # defaults already work for local SQLite

alembic upgrade head             # creates all tables
python -m app.db.seed            # seeds 39 concepts, 44 edges, 78 questions — safe to re-run

uvicorn app.main:app --reload    # http://localhost:8000
```

Swagger UI: **http://localhost:8000/docs**

> **Note on sentence-transformers:** the first time `embedding_service`
> actually needs the model, it downloads `all-MiniLM-L6-v2` from the
> Hugging Face Hub and caches it locally — needs internet on that first
> run only. If the download is ever unavailable, the service automatically
> falls back to a deterministic word-overlap similarity instead of
> crashing.

## 6. Local setup — frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # points at http://localhost:8000/api/v1 by default
npm run dev                        # http://localhost:3000
```

## 7. Running with / without a Groq API key

Leave `GROQ_API_KEY` blank in `backend/.env` and everything works —
mistake explanations, the study roadmap, and the AI mentor all return
realistic, complete mock responses (see `app/services/groq_service.py`).
Drop in a real key from [console.groq.com](https://console.groq.com) and
the exact same endpoints start returning live Groq output, with zero
frontend changes.

## 8. Deployment

### Frontend — Vercel
1. Import the repo into Vercel, set the **root directory** to `frontend`.
2. Add the env var `NEXT_PUBLIC_API_BASE_URL` = your deployed backend URL + `/api/v1`.
3. Deploy — `vercel.json` in `frontend/` is already configured for Next.js.

### Backend — Render or Railway
- **Render:** use the included `render.yaml` Blueprint (New → Blueprint,
  point at this repo). It provisions the web service + a managed Postgres
  database and wires `DATABASE_URL` automatically.
- **Railway:** New Project → Deploy from GitHub → set root directory to
  `backend` → it picks up `backend/railway.toml` and the `Dockerfile`.
- Either way, set `FRONTEND_ORIGIN` to your Vercel URL and (optionally)
  `GROQ_API_KEY` afterward.
- The Docker image runs `alembic upgrade head` before starting uvicorn —
  migrations, not `create_all()`, are the source of truth in production.

### Database — Supabase (or any Postgres)
```
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>:5432/<dbname>
```
No other code changes anywhere in the project — `app/core/database.py` is
the single seam that branches on SQLite vs. Postgres.

### All-in-one local Docker option
```bash
docker compose up --build
```

## 9. API reference

Full interactive reference at `/docs` (Swagger) once the backend is
running. Key route groups: `/api/v1/auth`, `/api/v1/concepts`,
`/api/v1/quiz` (including `/quiz/generate`), `/api/v1/diagnosis`,
`/api/v1/dashboard`, `/api/v1/ai` (including `/ai/roadmap/subject/{subject}`).

## 10. What's next (not yet built)

The initial pivot covers the core engine + four-subject dashboard. Still
on the roadmap per the product spec:

- Scaling the question bank from 78 to ~280 questions
- **Daily Spark** — 3 personalized daily quizzes prioritizing weak concepts
- **Interview Readiness Score** — a 0-100 composite across all 4 subjects with tiers (Beginner → Interview Ready → Product Company Ready)
- Deeper progress analytics (streaks, time spent, improvement trend charts)
- AI Mentor persona polish (interviewer-style follow-ups, complexity comparisons)

## 11. Design notes worth knowing

- The skill graph (39 concepts, 44 weighted prerequisite edges across 4
  subjects) and the question bank live in `backend/app/db/` as plain,
  readable Python data — easy to extend without touching any logic.
- shadcn/ui's own CLI registry host is blocked in some sandboxed/offline
  environments; `frontend/src/components/ui/` contains hand-built
  equivalents (Button, Card, Badge, Input, Tabs, Slider, etc.) using the
  same Radix + class-variance-authority + Tailwind pattern.
### AI Tutor Deployment Note
The AI Tutor feature requires additional computational resources for model processing. The deployed backend is hosted on Render's free tier, which has limited memory and may restart the service during AI Tutor requests. 

The feature has been fully tested and works correctly in the local environment. The deployed version includes the AI Tutor implementation, but occasional unavailability may occur due to free-tier hosting limitations.

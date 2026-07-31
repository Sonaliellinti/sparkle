# Production image for the FastAPI backend.
# Build:  docker build -t jee-diagnosis-backend .
# Run:    docker run -p 8000:8000 --env-file .env jee-diagnosis-backend
FROM python:3.12-slim

WORKDIR /app

# System deps needed by psycopg2 (Postgres) at build time
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ENVIRONMENT=production
EXPOSE 8000

# Apply migrations, then start the server. Using `alembic upgrade head`
# here (not create_all) is the production-correct path — see
# docs/PROJECT_PLAN.md §10.2.
CMD ["sh", "-c", "alembic upgrade head && python -m app.db.seed && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

# Auth & Cache for AI Apps

FastAPI backend with SQLite persistence, JWT auth, conversation ownership, and an in-memory cache.

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API docs: http://127.0.0.1:8000/docs

## Test

```bash
pytest -q
```

## Environment variables

- `DATABASE_URL` (default `sqlite:///./app.db`)
- `SECRET_KEY` (change in production)

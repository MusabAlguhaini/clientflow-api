# ClientFlow API

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

A multi-user **client & task tracker** REST API for freelancers and small agencies, built with **FastAPI**, **SQLAlchemy 2** and **JWT authentication**.

Each user registers, adds their clients, and tracks tasks per client with status, priority and due dates. Data is strictly isolated per user.

## Features

- JWT authentication (register / login / current user), PBKDF2-SHA256 password hashing
- Clients: full CRUD, search by name/company, pagination
- Tasks: CRUD under a client, filter by status / priority / client / overdue
- Dashboard endpoint with totals, per-status counts and overdue tasks
- Per-user data isolation (other users get `404`, never `403`, so existence is not leaked)
- Auto-generated interactive docs (Swagger UI at `/docs`)
- Tests (pytest), Dockerfile, GitHub Actions CI

## Quick start

```bash
git clone <this-repo-url> && cd clientflow-api
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                  # set SECRET_KEY
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs> for the interactive API docs.

### Docker

```bash
docker build -t clientflow-api .
docker run -p 8000:8000 -e SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')" clientflow-api
```

### Docker Compose (API + PostgreSQL)

```bash
export SECRET_KEY=$(openssl rand -hex 32)
docker compose up --build
```

The API is served at <http://localhost:8000/docs>, backed by a PostgreSQL 16 container with a persistent volume.

## Example usage

```bash
# Register and log in
curl -X POST localhost:8000/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","full_name":"Me","password":"password123"}'
TOKEN=$(curl -s -X POST localhost:8000/auth/login -d 'username=me@example.com&password=password123' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# Create a client and a task
curl -X POST localhost:8000/clients -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"Acme Corp","company":"Acme"}'
curl -X POST localhost:8000/clients/1/tasks -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title":"Design logo","priority":"high","due_date":"2026-12-01"}'

# Dashboard
curl localhost:8000/tasks/summary -H "Authorization: Bearer $TOKEN"
```

## API overview

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get JWT (OAuth2 password form) |
| GET | `/auth/me` | Current user |
| POST/GET | `/clients` | Create / list (`q`, `limit`, `offset`) |
| GET/PATCH/DELETE | `/clients/{id}` | Read / update / delete (cascades tasks) |
| POST | `/clients/{id}/tasks` | Create task for a client |
| GET | `/tasks` | List (`status`, `priority`, `client_id`, `overdue`, `limit`, `offset`) |
| GET | `/tasks/summary` | Totals, counts by status, overdue |
| GET/PATCH/DELETE | `/tasks/{id}` | Read / update / delete task |
| GET | `/health` | Health check |

## Project structure

```
app/
  main.py        # app factory, router wiring, startup
  config.py      # settings from env / .env
  database.py    # engine, session, Base
  models.py      # User, Client, Task
  schemas.py     # Pydantic request/response models
  security.py    # password hashing + JWT
  deps.py        # auth dependency, ownership checks
  routers/       # auth, clients, tasks
tests/           # pytest suite (in-memory SQLite)
```

## Configuration

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./clientflow.db` | Any SQLAlchemy URL (e.g. PostgreSQL) |
| `SECRET_KEY` | placeholder | **Change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime |

## Testing

```bash
pytest -q
```

## Roadmap

- Alembic migrations
- Refresh tokens and rate limiting
- Task comments and file attachments

## License

MIT
# ClientFlow API

[![CI](../../actions/workflows/ci.yml/badge.svg)](../../actions/workflows/ci.yml)

A multi-user **client & task tracker** REST API for freelancers and small agencies, built with **FastAPI**, **SQLAlchemy 2** and **JWT authentication**.

Each user registers, adds their clients, and tracks tasks per client with status, priority and due dates. Data is strictly isolated per user.

## Features

- JWT authentication (register / login / current user), PBKDF2-SHA256 password hashing
- Clients: full CRUD, search by name/company, pagination
- Tasks: CRUD under a client, filter by status / priority / client / overdue
- Dashboard endpoint with totals, per-status counts and overdue tasks
- Per-user data isolation (other users get `404`, never `403`, so existence is not leaked)
- Auto-generated interactive docs (Swagger UI at `/docs`)
- Tests (pytest), Dockerfile, GitHub Actions CI

## Quick start

```bash
git clone <this-repo-url> && cd clientflow-api
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                  # set SECRET_KEY
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs> for the interactive API docs.

### Docker

```bash
docker build -t clientflow-api .
docker run -p 8000:8000 -e SECRET_KEY="$(python -c 'import secrets;print(secrets.token_urlsafe(48))')" clientflow-api
```

## Example usage

```bash
# Register and log in
curl -X POST localhost:8000/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"me@example.com","full_name":"Me","password":"password123"}'
TOKEN=$(curl -s -X POST localhost:8000/auth/login -d 'username=me@example.com&password=password123' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# Create a client and a task
curl -X POST localhost:8000/clients -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"name":"Acme Corp","company":"Acme"}'
curl -X POST localhost:8000/clients/1/tasks -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title":"Design logo","priority":"high","due_date":"2026-12-01"}'

# Dashboard
curl localhost:8000/tasks/summary -H "Authorization: Bearer $TOKEN"
```

## API overview

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get JWT (OAuth2 password form) |
| GET | `/auth/me` | Current user |
| POST/GET | `/clients` | Create / list (`q`, `limit`, `offset`) |
| GET/PATCH/DELETE | `/clients/{id}` | Read / update / delete (cascades tasks) |
| POST | `/clients/{id}/tasks` | Create task for a client |
| GET | `/tasks` | List (`status`, `priority`, `client_id`, `overdue`, `limit`, `offset`) |
| GET | `/tasks/summary` | Totals, counts by status, overdue |
| GET/PATCH/DELETE | `/tasks/{id}` | Read / update / delete task |
| GET | `/health` | Health check |

## Project structure

```
app/
  main.py        # app factory, router wiring, startup
  config.py      # settings from env / .env
  database.py    # engine, session, Base
  models.py      # User, Client, Task
  schemas.py     # Pydantic request/response models
  security.py    # password hashing + JWT
  deps.py        # auth dependency, ownership checks
  routers/       # auth, clients, tasks
tests/           # pytest suite (in-memory SQLite)
```

## Configuration

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./clientflow.db` | Any SQLAlchemy URL (e.g. PostgreSQL) |
| `SECRET_KEY` | placeholder | **Change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Token lifetime |

## Testing

```bash
pytest -q
```

## Roadmap

- Alembic migrations
- Refresh tokens and rate limiting
- Task comments and file attachments
- Docker Compose with PostgreSQL

## License

MIT

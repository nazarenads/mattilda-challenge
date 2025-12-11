# FastAPI Boilerplate

A clean FastAPI project boilerplate with PostgreSQL, SQLAlchemy, and Alembic.

## Project Structure

```
boilerplate/
├── alembic/              # Database migrations
│   ├── versions/         # Migration files
│   ├── env.py
│   ├── README
│   └── script.py.mako
├── app/
│   ├── db/
│   │   ├── database.py   # Database connection and session
│   │   └── models.py     # SQLAlchemy models
│   ├── routers/
│   │   └── health.py     # Health check endpoint
│   ├── services/         # Business logic
│   ├── config.py         # Application settings
│   ├── dependencies.py   # FastAPI dependencies
│   ├── main.py           # FastAPI application
│   └── schemas.py        # Pydantic schemas
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### Running the Application

1. Start the application:
   ```bash
   docker compose up --build
   ```

2. The API will be available at:
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs

3. Stop the application:
   ```bash
   docker compose down
   ```

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /docs` - Swagger UI documentation

## Database Migrations

Run migrations inside the container:

```bash
docker compose exec app alembic upgrade head
```

Create a new migration:
```bash
docker compose exec app alembic revision --autogenerate -m "Description of changes"
```

Rollback last migration:
```bash
docker compose exec app alembic downgrade -1
```

## Configuration

Configuration is managed through environment variables in `docker-compose.yml`.

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@db:5432/boilerplate` |
| `DEBUG` | Enable debug mode | `true` |
| `ENVIRONMENT` | Environment name | `dev` |

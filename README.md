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
- **Schools:** `GET/POST /school/`, `GET/PUT/DELETE /school/{id}`, `GET /school/{id}/balance`
- **Students:** `GET/POST /student/`, `GET/PUT/DELETE /student/{id}`, `GET /student/{id}/balance`
- **Invoices:** `GET/POST /invoice/`, `GET/PUT/DELETE /invoice/{id}`
- **Payments:** `GET/POST /payment/`, `GET/PUT/DELETE /payment/{id}`
- **Payment Allocations:** `GET/POST /payment-allocation/`, `GET/PUT/DELETE /payment-allocation/{id}`

## Seed Data

Populate the database with sample data for testing:

```bash
docker compose run --rm app python -m scripts.seed_data
```

This creates:
- 5 schools (Mexico and Colombia)
- ~50 students with random names
- ~120 invoices with various statuses (draft, pending, paid, partially_paid, overdue)
- ~40 payments (cash, card, bank_transfer)
- ~30 payment allocations
- Currencies: MXN (Mexican Peso) and COP (Colombian Peso)

**Note:** Running this command will clear existing data before seeding.

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

## Running Tests

Run all tests inside the container:

```bash
docker compose run --rm app pytest
```

Run tests with coverage report:

```bash
docker compose run --rm app pytest --cov=app --cov-report=term-missing
```

Run tests in verbose mode:

```bash
docker compose run --rm app pytest -v
```

## Configuration

Configuration is managed through environment variables. Copy `.env.example` to `.env` and adjust as needed.

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@db:5432/boilerplate` |
| `DEBUG` | Enable debug mode | `true` |
| `ENVIRONMENT` | Environment name | `dev` |

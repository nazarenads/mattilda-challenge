# School administration platform



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

## Authentication

The API uses JWT (JSON Web Token) authentication. Most endpoints require a valid token.

### Default Admin User

On startup, an admin user is automatically created with these default credentials:
- **Email:** `admin@admin.com`
- **Password:** `admin1234`


### Getting a Token

To authenticate, send a POST request to `/token` with `username` and `password` as **form data** (not JSON):

```bash
curl -X POST http://localhost:8000/token \
  -d "username=admin@admin.com" \
  -d "password=admin1234"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in the `Authorization` header for protected endpoints:

```bash
curl -X GET http://localhost:8000/school/ \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Swagger UI Authentication

1. Click the **"Authorize"** button (🔓) at the top of the Swagger UI
2. Enter `admin@admin.com` as username and `admin1234` as password
3. Click **"Authorize"**
4. All subsequent requests will include the token automatically

## API Endpoints

- `POST /token` - Get authentication token
- `GET /health` - Health check endpoint
- `GET /docs` - Swagger UI documentation
- **Users:** `GET/POST /user/`, `GET/PUT/DELETE /user/{id}` (admin only)
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

## Running Tests

Run all tests inside the container:

```bash
docker compose run --rm app pytest
```

Run tests with coverage report:

```bash
docker compose run --rm app pytest --cov=app --cov-report=term-missing
```


## Configuration

Configuration is managed through environment variables. Copy `.env.example` to `.env` and adjust as needed.

## Deployed application

This project API has been deployed using Railway and is live to access at: https://mattilda-challenge-production.up.railway.app/docs

There's also a frontend developed using v0 that consumes the API and is deployed at: https://v0-school-finance-application.vercel.app 

Use these credentials to log in:
- **Email:** `admin@admin.com`
- **Password:** `admin1234`


### Some final considerations: 

 In a real production payments system: 
 
 - Most of the payments will be received via webhooks, by batch creation via file upload or in a message queue and should be automatically allocated to the corresponding invoices, following business logic, this system only exposes a CRUD to create "payment_allocations" which is unrealistic. In a production system, we would need automated reconciliation between internal records and external payment provider data. This includes matching transactions, identifying discrepancies, and generating reconciliation reports.

 - It would also be ideal to have a scheduled job that runs daily at the end of the day to validate invoices with "pending" status, attempting to locate payments that correspond to those invoices and ensuring that the invoice statuses are up to date.

 - Financial records should use soft deletes (deleted_at timestamp) instead of hard deletes. This maintains audit integrity and allows for data recovery if needed.




# Playto Payout Engine

This is a production-grade implementation of a Payout Engine for Playto Pay, handling concurrent transactions safely with idempotency guarantees.

## Setup Instructions

### Backend (Django + PostgreSQL/SQLite + Redis + Celery)

1. Make sure you have Redis running (or use Docker Compose).
2. `cd backend`
3. `python -m venv venv`
4. `source venv/bin/activate` (or `.\venv\Scripts\activate` on Windows)
5. `pip install -r requirements.txt`
6. `python manage.py migrate`
7. `python seed.py` (Creates 3 merchants with initial balance. EX-id : 11111111-1111-1111-1111-111111111111)
8. 
9. `python manage.py runserver`

In a new terminal window, start Celery:
```bash
cd backend
source venv/bin/activate
celery -A config worker -l info -P solo
celery -A config beat -l info
```

*(Note: In the submission, settings.py is configured to use SQLite locally due to Docker environment limitations, but uses `dj_database_url` for PostgreSQL in production. The exact code uses DB aggregate functions and `SELECT FOR UPDATE` designed specifically for PostgreSQL).*

### Frontend (React + Vite + Tailwind)

1. `cd frontend`
2. `npm install`
3. `npm run dev`

Open `http://localhost:5173`. Enter the Merchant ID generated from the seed script (e.g. `python seed.py` output).

### Docker Compose (Optional)
If Docker is available:
`docker-compose up -d` to run PostgreSQL and Redis.

## Testing

Run tests to verify concurrency and idempotency:
```bash
cd backend
python manage.py test payouts
```
*(Note: Concurrency test expects PostgreSQL to pass successfully since SQLite locks the whole DB file, resulting in an `OperationalError` instead of `InsufficientFunds` exception).*

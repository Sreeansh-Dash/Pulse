# Pulse - Open Source Uptime Monitor

Pulse is a modern, open-source uptime monitoring solution designed to keep track of your websites and APIs. It pings your endpoints at regular intervals and provides a beautiful dashboard to visualize uptime, response times, and incident history.

## Architecture
- **Frontend**: React (Vite), TypeScript, Tailwind CSS, Recharts
- **Backend**: FastAPI (Python), SQLAlchemy (SQLite/Postgres), APScheduler
- **Worker**: Async background process for health checks
- **Pub/Sub & Queues**: Redis

## Prerequisites
- Node.js (v18+)
- Python 3.10+
- Docker & Docker Compose (for Redis & Postgres)

## Local Setup

### 1. Start Services
Run `docker-compose up -d` to start the Redis container (required for Pub/Sub and the worker queue).

### 2. Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --port 8000
```

### 3. Background Worker
In a new terminal:
```bash
cd backend
.\venv\Scripts\activate
# Set PYTHONPATH so it can resolve the 'app' module
$env:PYTHONPATH="."  # Windows Powershell
# export PYTHONPATH="."  # macOS/Linux
python ..\worker\worker.py
```

### 4. Frontend
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to view the dashboard!

## License
MIT License

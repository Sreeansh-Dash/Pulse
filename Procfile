web: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: set PYTHONPATH=backend && cd worker && python worker.py

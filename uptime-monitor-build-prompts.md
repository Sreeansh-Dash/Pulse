# Project: Pulse — Distributed Uptime & Performance Monitor

A self-hosted monitoring tool that tracks uptime, response time, and health of your own deployed projects (portfolio site, PromptWars deployment, APIs, etc.) across multiple checks running concurrently, with a live dashboard.

This doc is written as a set of prompts to feed an AI coding agent step by step. Run them in order. Don't skip the "why" notes — they're there so the agent doesn't over-engineer or under-engineer a step.

---

## End Goal

A working, deployed monitoring service that:
- Checks 10–20 of your own URLs/endpoints every N minutes
- Runs all checks concurrently instead of one-by-one (real speed difference, easy to demo)
- Safely aggregates results from multiple concurrent checks into shared stats without race conditions
- Distributes the actual check execution to separate worker processes via a job queue (not just one script doing everything)
- Shows a live dashboard: current status, response time graphs, uptime %, incident history
- Sends an alert (email or Discord/Slack webhook) when something goes down

**Concepts intentionally covered (pick 3, not all 4):**
1. **Concurrency** — `asyncio`/`aiohttp` checking many endpoints in parallel within a worker
2. **Synchronization** — locking/atomic updates when multiple concurrent tasks write to shared aggregate stats (avoiding race conditions on the "uptime %" and "last status" fields)
3. **Distributed systems (lightweight)** — a job queue (Redis) separates the scheduler from one or more worker processes, so checks can run on a different machine/process than the API/dashboard

**Deliberately NOT covering:** OS-level multi-threading. Asyncio concurrency is single-threaded (event loop based), which is a real and correct distinction — don't let the agent add `threading`/`multiprocessing` on top just to "check a box." Mixing all 4 concepts into one small project is what looks artificial on a resume; 3 used correctly is more credible than 4 used superficially.

---

## Architecture

```
                    ┌─────────────────┐
                    │   Scheduler      │  (runs every N min, pushes jobs)
                    └────────┬─────────┘
                             │ pushes check-jobs
                             ▼
                    ┌─────────────────┐
                    │   Redis Queue    │
                    └────────┬─────────┘
                             │ pops jobs
                             ▼
                  ┌──────────────────────┐
                  │   Worker Process(es)  │
                  │  asyncio + aiohttp    │  ← concurrency happens here
                  │  checks N urls at once│
                  └────────┬──────────────┘
                             │ writes results (with lock)
                             ▼
                  ┌──────────────────────┐
                  │   PostgreSQL / SQLite │  ← synchronized writes
                  └────────┬──────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   FastAPI Backend     │  (REST + WebSocket)
                  └────────┬──────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   React Dashboard     │
                  └──────────────────────┘
```

The key separation: the **scheduler** decides *when* to check, the **queue** decides *what gets checked where*, the **worker** decides *how fast* (concurrently), and the **backend** just reads/serves state. This separation is what makes the "distributed" claim legitimate — it's not one script doing everything.

---

## Tech Stack

**Backend**
- Python 3.11+
- FastAPI (REST API + WebSocket for live updates)
- `aiohttp` for making the actual HTTP checks (async, not requests-blocking)
- `asyncio.Lock` (or `asyncio.Semaphore` where appropriate) for synchronizing shared in-memory state during a check batch
- Redis (job queue — use `redis-py`'s async client, or RQ/Celery if you want it to look more "production")
- PostgreSQL (use SQLite locally for dev, Postgres in production — most free hosts give you a free Postgres instance)
- `SQLAlchemy` (async mode) as the ORM

**Worker**
- A separate Python process (`worker.py`) that long-polls Redis for jobs, runs the async check batch, writes results

**Frontend**
- React + Vite
- Tailwind for styling
- `recharts` for response-time graphs
- WebSocket client for live status updates (don't poll every 2 seconds — push updates instead)

**Alerting**
- Discord or Slack webhook (simplest, free, no email service signup needed) on status change (up→down or down→up)

---

## Deployment (No Railway)

Use this combination, all free-tier:
- **Backend + Worker**: Render (free web service for API, free background worker for the worker process) — or Fly.io if you want more control and a more "I configured infra myself" story
- **Redis**: Render's free Redis instance, or Upstash (serverless Redis, generous free tier, very common in real projects)
- **Postgres**: Render free Postgres, or Supabase free tier
- **Frontend**: Vercel or Netlify (static React build)

Note: Render's free tier spins down on inactivity — mention this honestly if asked in an interview, it's a normal constraint, not a flaw in your design.

---

## Step-by-Step Agent Prompts

Feed these to your AI coding agent one at a time. Each one assumes the previous step is done and working before moving on.

### Prompt 1 — Project scaffolding
```
Set up a monorepo with two folders: `backend/` (FastAPI app with async SQLAlchemy,
structured as app/api, app/models, app/services) and `frontend/` (React + Vite + Tailwind).
Add a `worker/` folder at root level for the standalone worker script.
Include a docker-compose.yml that spins up Postgres and Redis locally for development.
Do not add authentication yet. Do not add the dashboard UI yet — just scaffolding and a
health-check endpoint at GET /health.
```

### Prompt 2 — Data models
```
In backend/app/models, create SQLAlchemy models for:
- Monitor (id, name, url, check_interval_seconds, created_at)
- CheckResult (id, monitor_id FK, status [up/down], response_time_ms, checked_at, status_code)
- Incident (id, monitor_id FK, started_at, resolved_at nullable)
Write an Alembic migration for these. Keep it minimal — no extra fields beyond what's listed.
```

### Prompt 3 — Async check logic with concurrency
```
In backend/app/services/checker.py, write an async function `check_all_monitors(monitors: list)`
that uses aiohttp and asyncio.gather to check ALL monitors concurrently (not sequentially) within
a single batch, with a per-request timeout of 10 seconds. Each check should record response time
and status. Add a basic test that proves checking 10 monitors concurrently takes roughly as long
as the slowest single check, not the sum of all checks — this is the actual evidence of concurrency,
write it as a real test, not a comment.
```

### Prompt 4 — Synchronized shared state
```
Now extend checker.py so that after each individual check completes, the result is written
immediately to a shared in-memory stats dict (live_status) that the WebSocket layer reads from.
Because multiple checks finish at unpredictable times and write to this shared dict concurrently,
protect writes with an asyncio.Lock so two checks finishing at the same instant can't corrupt
the dict or cause a lost update. Explain in a code comment exactly which race condition this
lock prevents — be specific, not generic.
```

### Prompt 5 — Redis job queue + worker process
```
Create worker/worker.py as a standalone script separate from the FastAPI app. It should:
1. Connect to Redis
2. Block-pop jobs from a queue named "check-jobs" (a job = a monitor_id or batch of monitor_ids)
3. Run check_all_monitors on that batch
4. Write results to Postgres
5. Push a small "status changed" event to a Redis pub/sub channel for the backend to relay over WebSocket
Also create backend/app/services/scheduler.py — a simple loop (APScheduler or a basic asyncio loop)
that, every check_interval_seconds, pushes a job per monitor onto the Redis queue rather than
checking directly. The backend API process and the worker process must be runnable as two
completely separate processes (prove this by giving me two separate run commands / Procfile entries).
```

### Prompt 6 — WebSocket live updates
```
Add a WebSocket endpoint /ws/status to the FastAPI backend that subscribes to the Redis pub/sub
channel from the worker and pushes status-changed events to connected clients in real time.
Don't have the frontend poll an HTTP endpoint every few seconds — it should receive pushed updates.
```

### Prompt 7 — Dashboard frontend
```
Build the React dashboard with: a card per monitor showing current status (up/down), a
24-hour response-time line chart using recharts, uptime percentage over last 24h/7d/30d,
and an incident history list. Use the WebSocket connection for live status, and a regular
REST call for historical chart data. Keep styling clean and minimal — no heavy component
libraries beyond Tailwind.
```

### Prompt 8 — Alerting
```
Add a webhook notifier (Discord webhook URL via env var) that fires when a monitor transitions
from up to down or down to up. Debounce so a single flaky check doesn't trigger a false alert —
require 2 consecutive failures before marking "down" and alerting.
```

### Prompt 9 — Deployment config
```
Add render.yaml (or fly.toml if using Fly.io) configuring: the FastAPI backend as a web service,
worker.py as a background worker service, and references to a managed Postgres and Redis (Upstash).
Add a separate deployment config for the frontend on Vercel, with the API URL as an environment
variable, not hardcoded. Write a short DEPLOY.md with the exact steps to deploy both, including
environment variables needed.
```

---

## Expected Results (what to actually capture for your resume/portfolio writeup)

- Concrete before/after timing: "checking 15 endpoints sequentially took ~9s, checking them concurrently took ~1.2s" — get a real number, don't estimate it
- Uptime % for your own real deployed projects over a real time window (run it for at least a week before screenshotting)
- A screenshot of the live dashboard with real data, not mock data
- One real incident, even a small one (your own portfolio site going down briefly, or a deliberate test) showing the alert firing and the incident log capturing it

---

## Mistakes to Avoid

- Don't fake the "distributed" angle by running everything in one process and just calling it distributed — the worker and the API must actually be separable processes, ideally even deployed as separate services.
- Don't add multi-threading on top of asyncio "to be safe" — it's both unnecessary and exposes that you added it just to tick a box, not because it solved a real problem.
- Don't poll the database from the frontend every couple of seconds and call it "real-time" — that's polling, not concurrency/distribution, and it's an easy thing for an interviewer to probe.
- Don't skip writing the timing test in Prompt 3 — "I added concurrency" without measured proof is a weak interview answer; "Here's the test that proves it" is a strong one.
- Don't over-claim in your resume bullet — say what you actually built (async I/O, job queue, lock-protected shared state), not buzzwords like "Kubernetes" or "microservices" that aren't in this stack.
- Don't leave the Redis/Postgres credentials in code — use environment variables from day one, it's a basic hygiene thing interviewers do check for in a GitHub repo.

---

## Resume Bullet (draft once built, edit to match actual numbers)

> Built and deployed a distributed uptime-monitoring service with a Redis-backed job queue separating scheduler, worker, and API processes; used asyncio/aiohttp to check N endpoints concurrently (Xs → Ys reduction in batch check time) with lock-protected shared-state aggregation to prevent race conditions on live status updates.

# Pulse - Open Source Uptime Monitor

Pulse is a modern, high-performance uptime monitoring solution designed to keep track of your websites and APIs. It pings your endpoints at regular intervals and provides a beautiful dashboard to visualize uptime, response times, and incident history in real-time.

## 🚀 How It Works (The Pipeline)
The system operates on a highly concurrent background scheduling pipeline:
1. **Background Scheduler (`APScheduler`)**: Runs continuously in the background of the FastAPI web process, triggering health-check events at regular intervals.
2. **Concurrent Health Checks (`aiohttp` + `asyncio`)**: The checker fetches all registered monitors from the SQLite/PostgreSQL database and spawns concurrent, non-blocking HTTP requests to evaluate their health.
3. **State Synchronization (`LiveStatusStore`)**: The results (response times, HTTP status codes, up/down state) are safely synchronized and written into a thread-safe, in-memory cache protected by concurrency locks.
4. **Real-time Broadcast (`WebSockets`)**: When a monitor's state changes, the cache triggers an event to the `ConnectionManager`, which broadcasts the updated JSON payload to all connected frontend React clients via WebSockets, enabling real-time dashboard updates.
5. **Persistence (`SQLAlchemy`)**: The historical results of every ping are flushed to the database in bulk so the frontend can render accurate historical uptime charts.

---

## 🧠 Technical Highlights

This project was specifically designed to demonstrate advanced concepts in backend engineering:

### 1. Concurrency (Asynchronous I/O)
Monitoring dozens or hundreds of URLs sequentially is slow and inefficient. Pulse leverages **Python's `asyncio` event loop and `aiohttp`** to perform concurrent network requests. Instead of spawning heavy OS-level threads for each HTTP request, the application uses cooperative multitasking (`asyncio.gather`). This allows a single worker to pause execution while waiting for an HTTP response and pick up other requests, maximizing throughput and dramatically reducing CPU overhead.

### 2. Synchronization and Race Condition Prevention
The real-time status of all monitors is cached in memory to ensure the WebSocket connections can serve initial states instantly without hitting the database. Because background health-check tasks are constantly writing to this cache while WebSocket routes are simultaneously reading from it, the application uses an **`asyncio.Lock()`**. This synchronization primitive ensures mutual exclusion, preventing race conditions, dirty reads, and guaranteeing data integrity across the concurrent tasks.

### 3. Architecting Distributed Systems (Adaptability)
While the current deployed version is bundled as a single-process monolith to minimize cloud hosting costs (perfect for the free tier on Render), the architecture was initially built—and can easily be scaled back—into a true **Distributed System**. The codebase inherently supports decoupling the `Scheduler/Worker` from the `Web API` using **Redis** as a distributed message broker:
- **Task Queues**: Pushing URLs to a Redis List (`lpush`/`brpop`) for fleets of stateless background workers to consume.
- **Pub/Sub**: Workers publishing health updates to a Redis channel, allowing multiple API nodes to subscribe and broadcast to their respective WebSocket clients.

## 🛠️ Local Setup

### 1. Backend
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --port 8000
```

### 2. Frontend
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to view the dashboard!

## License
MIT License

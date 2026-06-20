import asyncio
import time
import json
import aiohttp
from typing import List
from datetime import datetime, timezone
from app.models.models import Monitor, CheckResult

class LiveStatusStore:
    """
    In-memory dict of current status per monitor, read by the WebSocket layer.
    
    Holds the current real-time state of all monitors.
    Protected by asyncio.Lock since it's shared across the app.
    """
    def __init__(self):
        self._data: dict[str, dict] = {}
        self._lock = asyncio.Lock()
        
    async def update(self, monitor_id: str, result: CheckResult, url: str, name: str):
        async with self._lock:
            existing = self._data.get(monitor_id, {})
            consecutive_failures = existing.get("consecutive_failures", 0)
            
            if result.status == "down":
                consecutive_failures += 1
            else:
                consecutive_failures = 0
                
            self._data[monitor_id] = {
                "monitor_id": monitor_id,
                "url": url,
                "name": name,
                "status": result.status,
                "response_time_ms": result.response_time_ms,
                "status_code": result.status_code,
                "last_checked": result.checked_at.isoformat() if hasattr(result.checked_at, 'isoformat') else str(result.checked_at),
                "consecutive_failures": consecutive_failures,
                "previous_status": existing.get("status"),
            }
            
            new_state = self._data[monitor_id]
            
        from app.api.websocket import manager
        event = {
            "monitor_id": monitor_id,
            **new_state
        }
        asyncio.create_task(manager.broadcast(event))
    
    async def get_all(self) -> dict[str, dict]:
        async with self._lock:
            return dict(self._data)
    
    async def get(self, monitor_id: str) -> dict | None:
        async with self._lock:
            return self._data.get(monitor_id)

live_status_store = LiveStatusStore()

async def check_single_monitor(session: aiohttp.ClientSession, monitor: Monitor) -> CheckResult:
    """Check a single URL, record response time and status."""
    start = time.monotonic()
    
    try:
        async with session.get(monitor.url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            elapsed_ms = (time.monotonic() - start) * 1000
            
            # Optionally read body to ensure request finishes
            await resp.read()
            
            result = CheckResult(
                monitor_id=str(monitor.id),
                status="up" if resp.status < 400 else "down",
                response_time_ms=elapsed_ms,
                status_code=resp.status,
                checked_at=datetime.now(timezone.utc)
            )
    except (aiohttp.ClientError, asyncio.TimeoutError):
        elapsed_ms = (time.monotonic() - start) * 1000
        result = CheckResult(
            monitor_id=str(monitor.id),
            status="down",
            response_time_ms=elapsed_ms,
            status_code=None,
            checked_at=datetime.now(timezone.utc)
        )
    except Exception as e:
        elapsed_ms = (time.monotonic() - start) * 1000
        result = CheckResult(
            monitor_id=str(monitor.id),
            status="down",
            response_time_ms=elapsed_ms,
            status_code=None,
            checked_at=datetime.now(timezone.utc)
        )
    
    # Update live status immediately
    await live_status_store.update(str(monitor.id), result, monitor.url, monitor.name)
    return result

async def check_all_monitors(monitors: List[Monitor]) -> List[CheckResult]:
    """Check ALL monitors concurrently using asyncio.gather."""
    async with aiohttp.ClientSession() as session:
        tasks = [check_single_monitor(session, m) for m in monitors]
        results = await asyncio.gather(*tasks)
    return list(results)

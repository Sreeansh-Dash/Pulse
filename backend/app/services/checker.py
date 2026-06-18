import asyncio
import time
import json
import aiohttp
from typing import List
from app.models.models import Monitor, CheckResult
from app.services.redis_client import get_redis_client

class LiveStatusStore:
    """
    In-memory dict of current status per monitor, read by the WebSocket layer.
    
    Holds the current real-time state of all monitors in Redis.
    """
    async def update(self, monitor_id: str, result: CheckResult, url: str, name: str):
        redis = await get_redis_client()
        
        # Get existing state from Redis
        existing_str = await redis.hget("live_status", monitor_id)
        existing = json.loads(existing_str) if existing_str else {}
        
        consecutive_failures = existing.get("consecutive_failures", 0)
        
        if result.status == "down":
            consecutive_failures += 1
        else:
            consecutive_failures = 0
            
        new_state = {
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
        
        # Save back to Redis
        await redis.hset("live_status", monitor_id, json.dumps(new_state))
        
        # Publish state via Redis
        event = {
            "monitor_id": monitor_id,
            **new_state
        }
        await redis.publish("monitor-status", json.dumps(event))
    
    async def get_all(self) -> dict[str, dict]:
        redis = await get_redis_client()
        raw_data = await redis.hgetall("live_status")
        return {k: json.loads(v) for k, v in raw_data.items()}
    
    async def get(self, monitor_id: str) -> dict | None:
        redis = await get_redis_client()
        val = await redis.hget("live_status", monitor_id)
        return json.loads(val) if val else None

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
            )
    except (aiohttp.ClientError, asyncio.TimeoutError):
        elapsed_ms = (time.monotonic() - start) * 1000
        result = CheckResult(
            monitor_id=str(monitor.id),
            status="down",
            response_time_ms=elapsed_ms,
            status_code=None,
        )
    except Exception as e:
        elapsed_ms = (time.monotonic() - start) * 1000
        result = CheckResult(
            monitor_id=str(monitor.id),
            status="down",
            response_time_ms=elapsed_ms,
            status_code=None,
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

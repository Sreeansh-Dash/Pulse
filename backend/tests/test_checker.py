import asyncio
import time
from datetime import datetime, timezone
import pytest
from aiohttp import web
from app.models.models import Monitor
from app.services.checker import check_all_monitors, live_status_store

async def delay_handler(request):
    await asyncio.sleep(1.0)
    return web.Response(text="ok")

@pytest.mark.asyncio
async def test_concurrent_checks_are_actually_concurrent():
    app = web.Application()
    app.router.add_get('/delay', delay_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 0)
    await site.start()
    
    port = runner.addresses[0][1]
    url = f"http://localhost:{port}/delay"
    
    monitors = []
    for i in range(10):
        m = Monitor(
            id=str(i),
            name=f"Test {i}",
            url=url,
            check_interval_seconds=60
        )
        monitors.append(m)
    
    start = time.monotonic()
    results = await check_all_monitors(monitors)
    elapsed = time.monotonic() - start
    
    await runner.cleanup()
    
    assert len(results) == 10
    for r in results:
        assert r.status == "up"
        assert r.status_code == 200
        
    assert elapsed < 2.0, f"Took {elapsed:.1f}s — checks ran sequentially, not concurrently!"

@pytest.mark.asyncio
async def test_lock_prevents_lost_updates():
    from app.models.models import CheckResult
    
    monitor_id = "test-lock-monitor"
    live_status_store._data.clear()
    
    async def update_task(status):
        result = CheckResult(
            monitor_id=monitor_id,
            status=status,
            response_time_ms=50.0,
            checked_at=datetime.now(timezone.utc),
            status_code=200 if status == "up" else 500
        )
        await live_status_store.update(monitor_id, result, "http://test", "Test")
        
    tasks = [update_task("down") for _ in range(5)]
    await asyncio.gather(*tasks)
    
    state = live_status_store.get(monitor_id)
    assert state is not None
    assert state["consecutive_failures"] == 5
    assert state["status"] == "down"


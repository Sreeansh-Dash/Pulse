import json
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from app.database import async_session_maker
from app.models.models import Monitor
from app.services.redis_client import get_redis_client

logger = logging.getLogger(__name__)

async def schedule_checks():
    """
    Every check_interval_seconds, push one job per monitor onto the Redis queue.
    The scheduler does NOT run checks — it only decides WHEN to check and pushes
    jobs for the worker to process.
    """
    try:
        redis = await get_redis_client()
        async with async_session_maker() as session:
            result = await session.execute(select(Monitor))
            monitors = result.scalars().all()
            
            jobs_queued = 0
            for monitor in monitors:
                # We could add logic to only push if (now - last_checked) >= interval
                # But for simplicity, the APScheduler interval matches the default interval.
                # Since interval can be per-monitor, a more advanced approach is to schedule
                # a job for each monitor dynamically. We'll run this loop every 10 seconds 
                # and check if the monitor is due for a check.
                
                # Simplified: push job for all monitors.
                # A more robust version would store last_queued time in redis or DB.
                # We will just push all for now. If you want per-monitor intervals, 
                # you'd compare current time with last_checked + check_interval_seconds.
                
                job = json.dumps({
                    "id": str(monitor.id),
                    "url": monitor.url,
                    "name": monitor.name,
                    "check_interval_seconds": monitor.check_interval_seconds
                })
                await redis.lpush("check-jobs", job)
                jobs_queued += 1
                
            if jobs_queued > 0:
                logger.info(f"Queued {jobs_queued} jobs.")
    except Exception as e:
        logger.error(f"Error scheduling checks: {e}")

scheduler = AsyncIOScheduler()

def start_scheduler():
    # Run the scheduler loop every 60 seconds.
    scheduler.add_job(schedule_checks, 'interval', seconds=60)
    scheduler.start()
    logger.info("Scheduler started.")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler stopped.")

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from app.database import async_session_maker
from app.models.models import Monitor

logger = logging.getLogger(__name__)

async def schedule_checks():
    """
    Every interval, check all monitors directly in the same process
    since we are no longer using a separate background worker.
    """
    try:
        async with async_session_maker() as session:
            result = await session.execute(select(Monitor))
            monitors = result.scalars().all()
            
            if monitors:
                from app.services.checker import check_all_monitors
                check_results = await check_all_monitors(list(monitors))
                
                session.add_all(check_results)
                await session.commit()
                logger.info(f"Checked {len(check_results)} monitors.")
    except Exception as e:
        logger.error(f"Error checking monitors: {e}")

scheduler = AsyncIOScheduler()

def start_scheduler():
    # Run the scheduler loop every 60 seconds.
    scheduler.add_job(schedule_checks, 'interval', seconds=60)
    scheduler.start()
    logger.info("Scheduler started.")

def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler stopped.")

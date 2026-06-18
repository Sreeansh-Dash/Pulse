import asyncio
import json
import logging
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.services.checker import check_all_monitors
from app.models.models import Monitor
from app.config import settings
from redis import asyncio as aioredis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Worker process starting...")
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    logger.info("Connected to Redis and Database. Waiting for jobs...")
    
    while True:
        try:
            # Block-pop jobs from queue
            # brpop returns a tuple (queue_name, data) or None if timeout
            result = await redis.brpop("check-jobs", timeout=30)
            
            batch = []
            if result:
                batch.append(json.loads(result[1]))
                
                # Drain any remaining jobs without blocking
                while True:
                    next_job = await redis.rpop("check-jobs")
                    if not next_job:
                        break
                    batch.append(json.loads(next_job))
            
            if batch:
                logger.info(f"Worker processing batch of {len(batch)} jobs...")
                
                # Reconstruct Monitor objects for the checker
                monitors = []
                for job in batch:
                    m = Monitor(
                        id=job["id"],
                        url=job["url"],
                        name=job["name"],
                        check_interval_seconds=job.get("check_interval_seconds", 120)
                    )
                    monitors.append(m)
                
                # Check them all concurrently
                check_results = await check_all_monitors(monitors)
                
                # Save to database
                async with async_session() as session:
                    session.add_all(check_results)
                    await session.commit()
                
                # Publish changes to redis pub/sub
                for r in check_results:
                    event = {
                        "monitor_id": str(r.monitor_id),
                        "status": r.status,
                        "response_time_ms": r.response_time_ms,
                        "checked_at": r.checked_at.isoformat() if hasattr(r.checked_at, 'isoformat') else str(r.checked_at)
                    }
                    await redis.publish("monitor-status", json.dumps(event))
                    
                logger.info(f"Batch completed. Saved {len(check_results)} results.")
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        # If running from root directory, ensure pythonpath is correct
        # Worker shouldn't rely on FastAPI directly, but uses models.
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped.")

import httpx
import logging
from datetime import datetime, timezone
from app.models.models import Monitor, CheckResult, Incident
from app.database import async_session_maker
from app.config import settings

logger = logging.getLogger(__name__)

class DiscordAlerter:
    """
    Sends alerts via Discord webhook on monitor status transitions.
    """
    
    async def evaluate_and_alert(self, monitor_id: str, result: CheckResult, live_status: dict, url: str, name: str):
        if not settings.DISCORD_WEBHOOK_URL:
            return
            
        consecutive_failures = live_status.get("consecutive_failures", 0)
        previous_status = live_status.get("previous_status", "up") # Default to up
        
        # DOWN alert: only after 2 consecutive failures
        if result.status == "down" and consecutive_failures == 2 and previous_status != "down":
            await self._send_alert(name, url, "DOWN", result)
            await self._create_incident(monitor_id)
        
        # UP alert: immediately when recovering from down
        elif result.status == "up" and previous_status == "down":
            await self._send_alert(name, url, "UP (recovered)", result)
            await self._resolve_incident(monitor_id)

    async def _send_alert(self, name: str, url: str, status_msg: str, result: CheckResult):
        color = 15548997 if status_msg == "DOWN" else 5763719 # Red vs Green
        embed = {
            "title": f"Monitor {status_msg}: {name}",
            "description": f"URL: {url}",
            "color": color,
            "fields": [
                {"name": "Status Code", "value": str(result.status_code) if result.status_code else "N/A", "inline": True},
                {"name": "Response Time", "value": f"{result.response_time_ms:.1f} ms", "inline": True},
                {"name": "Timestamp", "value": str(datetime.now(timezone.utc)), "inline": False}
            ]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                await client.post(settings.DISCORD_WEBHOOK_URL, json={"embeds": [embed]})
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")

    async def _create_incident(self, monitor_id: str):
        async with async_session_maker() as session:
            incident = Incident(monitor_id=monitor_id)
            session.add(incident)
            await session.commit()
            
    async def _resolve_incident(self, monitor_id: str):
        async with async_session_maker() as session:
            from sqlalchemy import select, desc
            stmt = select(Incident).where(Incident.monitor_id == monitor_id, Incident.resolved_at.is_(None)).order_by(desc(Incident.started_at))
            result = await session.execute(stmt)
            incident = result.scalars().first()
            if incident:
                incident.resolved_at = datetime.now(timezone.utc)
                await session.commit()

discord_alerter = DiscordAlerter()

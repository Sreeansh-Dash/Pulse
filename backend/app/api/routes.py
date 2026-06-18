from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime, timedelta, timezone

from app.database import get_db_session
from app.models.models import Monitor, CheckResult, Incident
from app.services.checker import live_status_store

router = APIRouter()

@router.get("/api/monitors")
async def get_monitors(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(select(Monitor).order_by(Monitor.created_at))
    monitors = result.scalars().all()
    
    response = []
    live_data = await live_status_store.get_all()
    for m in monitors:
        data = {
            "id": str(m.id),
            "name": m.name,
            "url": m.url,
            "check_interval_seconds": m.check_interval_seconds,
            "created_at": m.created_at
        }
        if str(m.id) in live_data:
            data.update(live_data[str(m.id)])
        response.append(data)
    
    return response

@router.get("/api/monitors/{monitor_id}/results")
async def get_monitor_results(monitor_id: str, hours: int = 24, session: AsyncSession = Depends(get_db_session)):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    stmt = select(CheckResult).where(
        CheckResult.monitor_id == monitor_id,
        CheckResult.checked_at >= cutoff
    ).order_by(CheckResult.checked_at)
    
    result = await session.execute(stmt)
    results = result.scalars().all()
    return [{"checked_at": r.checked_at, "response_time_ms": r.response_time_ms, "status": r.status} for r in results]

@router.get("/api/monitors/{monitor_id}/uptime")
async def get_monitor_uptime(monitor_id: str, session: AsyncSession = Depends(get_db_session)):
    now = datetime.now(timezone.utc)
    periods = {"24h": 24, "7d": 24 * 7, "30d": 24 * 30}
    uptimes = {}
    
    for label, hours in periods.items():
        cutoff = now - timedelta(hours=hours)
        stmt = select(
            func.count().label("total"),
            func.sum(case((CheckResult.status == 'up', 1), else_=0)).label("up")
        ).where(
            CheckResult.monitor_id == monitor_id,
            CheckResult.checked_at >= cutoff
        )
        # Fix: Need to import case from sqlalchemy
        from sqlalchemy import case
        
        result = await session.execute(stmt)
        row = result.first()
        total = row.total if row else 0
        up = row.up if row else 0
        uptimes[label] = (up / total * 100) if total > 0 else 100.0
        
    return uptimes

@router.get("/api/incidents")
async def get_incidents(session: AsyncSession = Depends(get_db_session)):
    stmt = select(Incident).order_by(desc(Incident.started_at)).limit(50)
    result = await session.execute(stmt)
    incidents = result.scalars().all()
    
    # We could join with monitors to get name, doing manually here for speed
    monitor_ids = list(set([i.monitor_id for i in incidents]))
    m_stmt = select(Monitor).where(Monitor.id.in_(monitor_ids))
    m_result = await session.execute(m_stmt)
    monitors_map = {str(m.id): m.name for m in m_result.scalars().all()}
    
    response = []
    for i in incidents:
        response.append({
            "id": i.id,
            "monitor_id": i.monitor_id,
            "monitor_name": monitors_map.get(str(i.monitor_id), "Unknown"),
            "started_at": i.started_at,
            "resolved_at": i.resolved_at
        })
    return response

import pytest
from app.services.alerter import discord_alerter
from app.models.models import CheckResult
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_alerter_debounce(monkeypatch):
    alerts_sent = []
    
    async def mock_send_alert(name, url, status_msg, result):
        alerts_sent.append((status_msg, result))
        
    async def mock_create_incident(monitor_id):
        pass
        
    async def mock_resolve_incident(monitor_id):
        pass

    monkeypatch.setattr(discord_alerter, "_send_alert", mock_send_alert)
    monkeypatch.setattr(discord_alerter, "_create_incident", mock_create_incident)
    monkeypatch.setattr(discord_alerter, "_resolve_incident", mock_resolve_incident)
    
    # Enable alerts
    from app.config import settings
    settings.DISCORD_WEBHOOK_URL = "http://test-webhook"

    monitor_id = "123"
    url = "http://test"
    name = "Test"
    
    result_down = CheckResult(status="down", response_time_ms=100.0, checked_at=datetime.now(timezone.utc), status_code=500)
    result_up = CheckResult(status="up", response_time_ms=50.0, checked_at=datetime.now(timezone.utc), status_code=200)
    
    # 1. First failure -> shouldn't alert
    live_status = {"consecutive_failures": 1, "previous_status": "up"}
    await discord_alerter.evaluate_and_alert(monitor_id, result_down, live_status, url, name)
    assert len(alerts_sent) == 0
    
    # 2. Second failure -> should alert DOWN
    live_status = {"consecutive_failures": 2, "previous_status": "up"}
    await discord_alerter.evaluate_and_alert(monitor_id, result_down, live_status, url, name)
    assert len(alerts_sent) == 1
    assert alerts_sent[0][0] == "DOWN"
    
    # 3. Third failure -> shouldn't alert again because previous_status is down
    live_status = {"consecutive_failures": 3, "previous_status": "down"}
    await discord_alerter.evaluate_and_alert(monitor_id, result_down, live_status, url, name)
    assert len(alerts_sent) == 1
    
    # 4. Recover -> should alert UP
    live_status = {"consecutive_failures": 0, "previous_status": "down"}
    await discord_alerter.evaluate_and_alert(monitor_id, result_up, live_status, url, name)
    assert len(alerts_sent) == 2
    assert alerts_sent[1][0] == "UP (recovered)"

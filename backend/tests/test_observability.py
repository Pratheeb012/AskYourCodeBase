import pytest
import os
import json
from app.services.observability import log_llm_transaction, LOG_FILE

@pytest.mark.asyncio
async def test_observability_logging():
    # Ensure file is fresh
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)
    
    log_llm_transaction(
        agent_name="test_agent",
        task="Test task",
        output="Test output",
        latency_ms=100
    )
    
    assert os.path.exists(LOG_FILE)
    
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        line = f.readline()
        data = json.loads(line)
        assert data["agent"] == "test_agent"
        assert data["task"] == "Test task"
        assert data["output"] == "Test output"
        assert data["latency_ms"] == 100

import json
import os
import time
from datetime import datetime
from app.core.config import settings

LOG_FILE = os.path.join(settings.DATA_DIR, "llm_traces.json")

def log_llm_transaction(
    agent_name: str,
    task: str,
    output: str,
    latency_ms: int,
    model: str = settings.GROQ_MODEL,
    metadata: dict = None
):
    """Log a single LLM transaction for observability and tracing."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent": agent_name,
        "model": model,
        "task": task,
        "output": output,
        "latency_ms": latency_ms,
        "metadata": metadata or {}
    }
    
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    
    # Append to JSON lines file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def get_recent_traces(limit: int = 50):
    if not os.path.exists(LOG_FILE):
        return []
    traces = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            traces.append(json.loads(line))
    return list(reversed(traces))[:limit]

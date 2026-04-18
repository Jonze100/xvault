"""
Natural Language Command API Route

POST /api/command — Parse and execute a plain-text command
"""

from fastapi import APIRouter
from pydantic import BaseModel

from orchestrator.graph import XVaultOrchestrator

router = APIRouter()

# Shared orchestrator instance (initialized once)
_orchestrator: XVaultOrchestrator | None = None


def get_orchestrator() -> XVaultOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = XVaultOrchestrator()
    return _orchestrator


class CommandRequest(BaseModel):
    command: str


@router.post("/command")
async def execute_command(body: CommandRequest):
    """
    Parse a natural language command and route to the appropriate agent(s).
    Examples:
    - "Rotate 10% to ETH" → orchestrator → signal + execution agents
    - "Pause signal agent" → agents API → toggle pause
    - "What is our risk score?" → portfolio agent → return current risk
    """
    from datetime import datetime, timezone
    try:
        orchestrator = get_orchestrator()
        result = await orchestrator.handle_command(body.command)
        return {
            "success": result.get("success", True),
            "data": result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        err_str = str(exc)
        # Surface billing / API key errors as a readable message
        if "credit balance" in err_str or "insufficient" in err_str.lower():
            msg = "Anthropic API credits exhausted — please top up at console.anthropic.com."
        elif "api_key" in err_str.lower() or "authentication" in err_str.lower():
            msg = "Anthropic API key invalid or missing."
        else:
            msg = f"Command error: {err_str[:120]}"
        return {
            "success": False,
            "data": {"success": False, "agent": "signal", "message": msg, "action": "error"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

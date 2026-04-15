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
    orchestrator = get_orchestrator()
    result = await orchestrator.handle_command(body.command)

    from datetime import datetime, timezone
    return {
        "success": result.get("success", True),
        "data": result,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

"""
ADK-compatible tool wrapper for character management.
This module provides simple callable functions for ADK agents.
"""

from typing import Dict, Any, Optional
from .tool import (
    ensure_combat_session_function,
)

async def ensure_combat_session_tool(
    server_id: str,
    player_id: str, 
    mob_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new character with required fields only."""
    return await ensure_combat_session_function(
        server_id=server_id,
        player_id=player_id,
        mob_name=mob_name,
    )

__all__ = ["ensure_combat_session_tool"]

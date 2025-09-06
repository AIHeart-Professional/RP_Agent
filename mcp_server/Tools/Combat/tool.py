import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from pymongo import MongoClient
from bson import ObjectId
import logging
from config.logging_config import setup_logging
from ..Mechanics.DAO import SessionDAO, CharacterDAO
setup_logging()
logger = logging.getLogger(__name__)

async def ensure_combat_session_function(
    server_id: str,
    player_id: str, 
    mob_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new combat session for the specified player.
    
    Required fields:
    - server_id: UUID string for the server
    - player_id: UUID string for the player
    Optional fields:
    - mob_name: Name of the mob to be included in the combat session (This tells us that this is to create a session)
    Returns:
    - Dict with success status and session ID or error message
    """
    try:
        try:
            # Step 1: Validate UUIDs
            uuid.UUID(server_id)
            uuid.UUID(player_id)
        except ValueError as e:
            # Step 1a: Return error if UUID is invalid
            return {
                "error": f"Invalid UUID format: {str(e)}"
            }
        session_dao = SessionDAO()
        character_dao = CharacterDAO()
        # Step 2: Retrieve active character data
        character_data = await character_dao.get_player(server_id, player_id)
        # Step 3: Return error if character is not found
        if not character_data:
            return {
                "error": "Character not found"
            }
        session_id = character_data["instances"]["session_id"]
        # Step 4: Check if session already exists and if mob_name is not provided, this tells us we want to check active combat session
        existing_session = await session_dao.retrieve_combat_session(server_id, session_id)
        if existing_session and not mob_name:
            return {"success": True, "session": existing_session}
        elif not existing_session and not mob_name:
            # Step 4a: Return message that user is already in a session
            return {"success": True, "message": "User is not in a combat session"}
        elif existing_session and mob_name:
            # Step 4b: Return that a new session can't be created because session already exists
            return {"success": True, "message": "User is already in a combat session"}
        else:
            # Step 4c: Obtain party data
            party_id = character_data["instances"]["party_id"]
            party = await session_dao.retrieve_party(server_id, party_id)
            # Step 4c1: If user is in a party
            if party:
                # Step 4c1a: If user is the leader of the party
                if party["leader"] == player_id:
                    # Step 4c1a1: Create a new combat session for the party
                    session = await session_dao.create_combat_session(server_id, player_id, mob_name, party_id)
                    # Step 4c1a2: Set all players in the parties instance to the new session
                    for player in party["players"]:
                        await character_dao.update_player(
                            server_id, 
                            player["character_id"], 
                            {"instances": {"session_id": session["_id"]}}
                        )

                else:
                    # Step 4c1a2: If user is not the leader, return error
                    return {
                        "error": "User is not the leader of the party, cannot create a combat encounter"
                    }
            else:
                # Step 4c2: Create a new combat session for the user
                session = await session_dao.create_combat_session(server_id, player_id, mob_name)
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create session: {str(e)}"
        }

# Export the synchronous functions
__all__ = ["ensure_session_function"]

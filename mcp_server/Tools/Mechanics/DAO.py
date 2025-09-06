# daos/mongo_character_dao.py
from typing import Optional, Dict, List, Union
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime

# MongoDB configuration
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "Veritas"

class MongoCharacterDAO:
    def __init__(self):
        self._client = MongoClient(MONGO_URI)
        self._collection = self._client[DB_NAME]["characters"]

    def get_by_player(self, server_id: str, player_id: str) -> Optional[Dict[str, object]]:
        return self._collection.find_one({"player.server_id": server_id, "player.player_id": player_id, "player.active": True})

    def get_by_ids(self, ids: List[str]) -> List[Dict[str, object]]:
        oids = [ObjectId(i) for i in ids]
        return list(self._collection.find({"_id": {"$in": oids}}))

    def create(self, payload: Dict[str, object]) -> Dict[str, object]:
        res = self._collection.insert_one(payload)
        return {**payload, "_id": str(res.inserted_id)}

class CharacterDAO:
    def __init__(self):
        self._client = MongoClient(MONGO_URI)
        self._collection = self._client[DB_NAME]["characters"]

    async def get_player(self, server_id: str, player_id: str, character_name: Optional[str] = None, character_id: Optional[str] = None) -> Optional[Dict[str, object]]:
        # Step 1: If character_name, get specified character on server
        if character_name:
            return self._collection.find_one({"player.server_id": server_id, "character.characters_name": character_name})
        # Step 2: If character_id, get specified character on the server
        elif character_id:
            return self._collection.find_one({"player.server_id": server_id, "_id": ObjectId(character_id)})
        # Step 3: If no character_name or character_id, get active character for player
        else:
            return self._collection.find_one({"player.server_id": server_id, "player.player_id": player_id, "player.active": True})

    async def update_player(self, server_id: str, player_id: str, update: Dict[str, object]) -> None:
        # Step 1: Update player
        self._collection.update_one({"player.server_id": server_id, "player.player_id": player_id}, {"$set": update})

class SessionDAO:
    def __init__(self):
        self._client = MongoClient(MONGO_URI)
        self._collection = self._client[DB_NAME]["sessions"]

    async def retrieve_combat_session(self, server_id: str, session_id: str) -> Optional[Dict[str, object]]:
        # Step 1: Get active session
        session = self._collection.find_one({
            "_id": ObjectId(session_id),
            "player.server_id": server_id
        })
        # Step 2: If session is found, return it
        if session:
            return session
        # Step 3a: If session is not found, return None
        else:
            return None

    async def retrieve_party(self, server_id: str, party_id: str) -> Optional[Dict[str, object]]:
        # Step 1: Get active session
        party = self._collection.find_one({
            "_id": ObjectId(party_id),
            "player.server_id": server_id
        })
        # Step 2: If session is found, return it
        if party:
            return party
        # Step 3a: If session is not found, return None
        else:
            return None

    async def create_combat_session(self, server_id: str, character_ids: Union[str, List[str]], mob_names: Optional[Union[str, List[str]]] = None, mob_ids: Optional[Union[str, List[str]]] = None) -> ObjectId:
        """
        Create a combat session with single or multiple players and mobs.
        
        Args:
            server_id: Server identifier
            character_ids: Single character_id (str) or list of character_ids
            mob_names: Single mob_name (str) or list of mob_names
            mob_ids: Single mob_id (str) or list of mob_ids
            
        Returns:
            ObjectId of the created session
        """
        # Step 1: Normalize character_ids to list
        if isinstance(character_ids, str):
            character_list = [character_ids]
        elif isinstance(character_ids, list):
            character_list = character_ids
        else:
            raise ValueError("character_ids must be string or list of strings")
        
        # Step 2: Normalize mob_names to list
        mob_names_list = []
        if mob_names is not None:
            if isinstance(mob_names, str):
                mob_names_list = [mob_names]
            elif isinstance(mob_names, list):
                mob_names_list = mob_names
            else:
                raise ValueError("mob_names must be string or list of strings")
        
        # Step 3: Normalize mob_ids to list
        mob_ids_list = []
        if mob_ids is not None:
            if isinstance(mob_ids, str):
                mob_ids_list = [mob_ids]
            elif isinstance(mob_ids, list):
                mob_ids_list = mob_ids
            else:
                raise ValueError("mob_ids must be string or list of strings")
        
        # Step 4: Create new session
        session = {
            "players": {
                "character_ids": character_list,
                "server_id": server_id
            },
            "mobs": {
                "mob_names": mob_names_list,
                "mob_ids": mob_ids_list
            },
            "instance": "combat",
            "meta": {
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
        }
        
        # Step 5: Insert session into database
        result = self._collection.insert_one(session)
        
        # Step 6: Return session ID
        return result
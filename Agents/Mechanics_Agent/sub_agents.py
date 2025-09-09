import os
import sys

# Add project root to Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from google.adk.agents import Agent
from mcp_server.Tools.Character.adk_tool import (
    create_character_tool,
    update_character_tool,
    get_character_tool,
    delete_character_tool
)
from mcp_server.Tools.Inventory.adk_tool import (
    get_inventory_tool,
    add_item_tool,
    remove_item_tool,
    equip_item_tool,
    unequip_item_tool,
    use_consumable_tool,
    transfer_item_tool,
    sort_inventory_tool,
    get_equipment_stats_tool
)
from mcp_server.Tools.Combat.adk_tool import (
    ensure_combat_session_tool
)
from mcp_server.Tools.Item.adk_tool import (
    get_item_tool,
    create_item_tool,
    update_item_tool,
    delete_item_tool
)
character_sub_agent = Agent(
    name="character_sub_agent",
    model="gemini-1.5-flash",
    description="Agent designed to handle character interactions.",
    instruction="You will take the users request and delegate it to the appropriate tools. Extract server_id and player_id (user_id) from the [CONTEXT] section of messages.",
    tools=[create_character_tool, update_character_tool, get_character_tool, delete_character_tool],
)

combat_sub_agent = Agent(
    name="combat_sub_agent",
    model="gemini-1.5-flash",
    description="Agent designed to handle combat interactions.",
    instruction="You will take the users request and delegate it to the appropriate tools. Extract server_id and player_id (user_id) from the [CONTEXT] section of messages.",
    tools=[ensure_combat_session_tool],
)

inventory_sub_agent = Agent(
    name="inventory_sub_agent",
    model="gemini-1.5-flash",
    description="Agent designed to handle inventory interactions.",
    instruction="You will take the users request and delegate it to the appropriate tools. Extract server_id and player_id (user_id) from the [CONTEXT] section of messages.",
    tools=[get_inventory_tool, add_item_tool, remove_item_tool, equip_item_tool, unequip_item_tool, use_consumable_tool, transfer_item_tool, sort_inventory_tool, get_equipment_stats_tool],
)

item_sub_agent = Agent(
    name="item_sub_agent",
    model="gemini-1.5-flash",
    description="Agent designed to handle item interactions.",
    instruction="You will take the users request and delegate it to the appropriate tools. Extract server_id and player_id (user_id) from the [CONTEXT] section of messages.",
    tools=[get_item_tool, create_item_tool, update_item_tool, delete_item_tool],
)

    
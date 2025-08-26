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

character_sub_agent = Agent(
    name="character_sub_agent",
    model="gemini-1.5-flash",
    description="Agent designed to handle character interactions for a roleplaying game.",
    instruction="You are an expert at managing characters for a roleplaying game. You can help with things such as editing character information, creating characters, and deleting characters.",
    tools=[create_character_tool, update_character_tool, get_character_tool, delete_character_tool],
)
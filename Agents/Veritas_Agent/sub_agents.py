import os
import sys

# Add project root to Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from google.adk.agents import Agent
from mcp_server.Tools.utility.utility_tools import discover_available_agents, delegate_to_agent, call_specific_agent

agent_delegator_sub_agent = Agent(
    name="agent_delegator_sub_agent",
    model="gemini-1.5-flash",
    description="Agent that delegates tasks to other A2A agents in the system.",
    instruction="""You are a task delegation specialist. When given a user request, you MUST use the delegate_to_agent() function to send the task to the appropriate external A2A agent. 

IMPORTANT: Do NOT try to transfer control to other agents directly. Always use the delegate_to_agent() tool function to communicate with external agents.

For character-related requests (create character, stats, leveling), use delegate_to_agent() to send the task to the Mechanics agent.
For inventory-related requests (items, equipment, inventory management), use delegate_to_agent() to send the task to the Mechanics agent.

Always call delegate_to_agent() with the full user request as the task_description parameter.""",
    tools=[discover_available_agents, delegate_to_agent, call_specific_agent],
    output_key="agent_response"
)
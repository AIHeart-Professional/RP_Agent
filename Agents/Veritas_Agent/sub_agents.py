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
    instruction="You are a task delegation specialist. When given a user request, you MUST immediately delegate it using delegate_to_agent().",
    tools=[discover_available_agents, delegate_to_agent, call_specific_agent],
    output_key="agent_response"
)
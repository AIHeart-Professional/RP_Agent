import asyncio
import aiohttp
import logging
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AgentInfo:
    """Information about a discovered A2A agent"""
    name: str
    description: str
    url: str
    skills: List[Dict]
    version: str = "1.0.0"

class A2AAgentDiscovery:
    """Discovers and manages A2A agents running on different ports"""
    
    def __init__(self):
        self.known_agents: Dict[str, AgentInfo] = {}
        self.agent_ports = [9998]  # Common A2A agent ports
        
    async def discover_agents(self) -> Dict[str, AgentInfo]:
        """Discover all available A2A agents by checking their agent card endpoints"""
        logger.info("Discovering A2A agents...")
        discovered = {}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
            for port in self.agent_ports:
                try:
                    agent_info = await self._check_agent_endpoint(session, port)
                    if agent_info:
                        discovered[agent_info.name] = agent_info
                        logger.info(f"Discovered agent: {agent_info.name} at port {port}")
                except Exception as e:
                    logger.error(f"No agent found on port {port}: {e}")
                    
        self.known_agents.update(discovered)
        return discovered
    
    async def _check_agent_endpoint(self, session: aiohttp.ClientSession, port: int) -> Optional[AgentInfo]:
        """Check if an agent is running on the given port"""
        url = f"http://localhost:{port}/.well-known/agent-card.json"
        logger.debug(f"Checking port {port}")        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Agent card received from port {port}: {data['name']}")
                    return AgentInfo(
                        name=data.get("name", f"agent_port_{port}"),
                        description=data.get("description", ""),
                        url=data.get("url", f"http://localhost:{port}"),
                        skills=data.get("skills", []),
                        version=data.get("version", "1.0.0")
                    )
                else:
                    logger.debug(f"Port {port} returned status {response.status}")
        except Exception as e:
            logger.error(f"Error checking port {port}: {e}")
        logger.debug(f"No agent found on port {port}")
        return None
    
    async def find_agent_for_task(self, task_description: str) -> Optional[AgentInfo]:
        """Find the best agent for a given task based on skills and description"""
        logger.debug(f"Finding agent for task: {task_description}")
        await self.discover_agents()  # Refresh agent list
        task_lower = task_description.lower()
        best_match = None
        best_score = 0
        for agent in self.known_agents.values():
            logger.debug(f"Checking agent: {agent.name}")
            score = 0
            # Check skills
            for skill in agent.skills:
                logger.debug(f"Checking skill: {skill.get('name', 'unknown')}")
                skill_name = skill.get("name", "").lower()
                skill_desc = skill.get("description", "").lower()
                skill_tags = [tag.lower() for tag in skill.get("tags", [])]
                
                # Score based on skill relevance
                if any(tag in task_lower for tag in skill_tags):
                    score += 3
                if any(word in task_lower for word in skill_name.split()):
                    score += 2
                if any(word in task_lower for word in skill_desc.split()):
                    score += 1
            
            # Check agent description
            desc_words = agent.description.lower().split()
            logger.debug(f"Checking agent description: {agent.description}")
            if any(word in task_lower for word in desc_words):
                score += 1
                
            if score > best_score:
                best_score = score
                best_match = agent
                
        return best_match
    
    async def call_agent_skill(self, agent_info: AgentInfo, skill_id: str, request_data: Dict) -> Dict:
        """Call a specific skill on an A2A agent"""
        logger.debug(f"Calling skill {skill_id} on agent {agent_info.name}")
        # For A2A agents created with to_a2a(), we need to call the /tasks endpoint
        url = agent_info.url.rstrip('/')
        
        # A2A agents expect a SendMessageRequest format
        message_text = request_data.get("task", request_data.get("user_query", ""))
        payload = {
            "id": str(uuid.uuid4()),
            "method": "message/send",
            "params": {
                "metadata": {
                    "server_id": "server",
                    "user_id": "user",
                    "session_id": "default_session"
                },
                "message": {
                    "messageId": str(uuid.uuid4()),
                    "role": "user",
                    "parts": [{
                        "type": "text",
                        "text": message_text
                    }]
                }
            }
        }
                
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            try:
                logger.debug(f"Calling skill {skill_id} on agent {agent_info.name} with payload: {payload}")
                async with session.post(url, json=payload) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        try:
                            logger.debug(f"Agent call successful with response: {response_text}")
                            return await response.json()
                        except:
                            # If not JSON, return as text
                            logger.error(f"Agent call failed, not a json format. response: {response_text}")
                            return {"response": response_text}
                    else:
                        logger.error(f"Agent call failed with status {response.status}: {response_text}")
                        return {"error": f"Agent call failed with status {response.status}: {response_text}"}
            except Exception as e:
                logger.error(f"Exception calling agent: {e}")
                return {"error": f"Failed to call agent: {str(e)}"}
    
    def get_available_agents(self) -> Dict[str, AgentInfo]:
        """Get all currently known agents"""
        logger.debug(f"Returning {len(self.known_agents)} agents")
        return self.known_agents.copy()
    
    def get_agent_capabilities_summary(self) -> str:
        """Get a summary of all available agents and their capabilities"""
        logger.debug(f"Returning agent capabilities summary")
        if not self.known_agents:
            return "No agents currently discovered."
        
        summary = "Available A2A Agents:\n"
        for name, agent in self.known_agents.items():
            logger.debug(f"Returning agent capabilities summary for {name}")
            summary += f"\n• {name}: {agent.description}\n"
            if agent.skills:
                summary += "  Skills:\n"
                for skill in agent.skills:
                    skill_name = skill.get("name", "Unknown")
                    skill_desc = skill.get("description", "")
                    summary += f"    - {skill_name}: {skill_desc}\n"
        logger.debug(f"Returning agent capabilities summary: {summary}")
        return summary

# Global discovery instance
agent_discovery = A2AAgentDiscovery()

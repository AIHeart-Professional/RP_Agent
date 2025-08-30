import importlib
import json
import logging
import uuid
import os
import sys
import asyncio
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from pathlib import Path

# ADK imports
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.agents import Agent
from google.genai import types
from sub_agents import (
    character_sub_agent
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure project root is on sys.path so `mcp_server` can be imported when ADK runs from Agents/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load environment variables from project root .env
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(PROJECT_ROOT) / ".env")
except ImportError:
    pass

# Configure API credentials (preserve if already set)
os.environ["GOOGLE_API_KEY"] = os.environ.get("GOOGLE_API_KEY", "")
if not os.environ["GOOGLE_API_KEY"]:
    logging.getLogger(__name__).warning(
        "GOOGLE_API_KEY is not set. Ensure it is present in your environment or .env file."
    )

class MechanicsAgent:
    def __init__(self):
        # Try to load from .env file
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            try:
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.environ.get("GOOGLE_API_KEY")
            except ImportError:
                pass

        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is required. Please set it in your environment or .env file.")
        
        os.environ["GOOGLE_API_KEY"] = api_key
        
        # Create the agent once during initialization
        self.agent = Agent(
            name="mechanics_agent",
            model="gemini-1.5-flash",
            description="Agent designed as a parent agent whose purpose is to delegate tasks to other agents.",
            instruction="You are a parent agent that immediately delegates all user requests to your sub-agent.",
            output_key="veritas",
            sub_agents=[character_sub_agent],
        )
        
        # Create session first
        self.session = InMemorySessionService()
        
        # Create runner with required arguments
        self.runner = Runner(
            app_name="mechanics_agent",
            agent=self.agent,
            session_service=self.session
        )

    async def invoke(self, message: str = "hello world"):
        """Process a message and return the agent's text response"""
        try:
            # Create a session
            user_id = str(uuid.uuid4())
            session = await self.session.create_session(
                app_name=self.runner.app_name,
                user_id=user_id
            )
            session_id = session.id
            
            # Convert message to Content format
            content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=message)],
            )
            
            # Run the agent with the message
            last_event = None
            async for event in self.runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                last_event = event
            
            # Extract response from the final event
            if last_event:
                # Try to get text response first
                if hasattr(last_event, 'text') and last_event.text:
                    return last_event.text
                
                # Handle Content objects with parts
                if hasattr(last_event, 'content') and hasattr(last_event.content, 'parts'):
                    text_parts = []
                    for part in last_event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                        elif hasattr(part, 'function_call'):
                            # Handle function call results
                            func_call = part.function_call
                            if hasattr(func_call, 'name') and hasattr(func_call, 'args'):
                                text_parts.append(f"Function call: {func_call.name} with args: {func_call.args}")
                    
                    if text_parts:
                        return "\n".join(text_parts)
                
                # Fallback to content attribute
                elif hasattr(last_event, 'content'):
                    return str(last_event.content)
                
                # Last resort - convert event to string
                return str(last_event)
            
            return "No response received"
                
        except Exception as e:
            logger.error(f"Error in agent invoke: {e}")
            return f"Error processing request: {str(e)}"

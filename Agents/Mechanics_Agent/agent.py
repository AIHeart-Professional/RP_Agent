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
    character_sub_agent,
    combat_sub_agent
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
        

        self.agent = Agent(
            name="mechanics_agent",
            model="gemini-1.5-flash",
            description="Agent designed as a parent agent whose purpose is to delegate tasks to other agents.",
            instruction="You are a mechanics agent that focuses on the logical application of user requests. You will always delegate requests to your sub-agents, never perform actions yourself.",
            output_key="mechanics",
            sub_agents=[character_sub_agent, combat_sub_agent]
        )
        
        # Create session first
        self.session = InMemorySessionService()
        
        # Create runner with required arguments
        self.runner = Runner(
            app_name="mechanics_agent",
            agent=self.agent,
            session_service=self.session
        )
from typing_extensions import override
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from agent import MechanicsAgent
from google.genai import types
import uuid
import logging
import warnings
from config.logging_config import setup_logging
from utils.agent_display import AgentLogger

# Optional context manager import
try:
    from Agents.context_manager import context_manager
    CONTEXT_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Context manager not available: {e}")
    context_manager = None
    CONTEXT_AVAILABLE = False

setup_logging()
logger = logging.getLogger(__name__)

# Suppress the specific Google GenAI warning about non-text parts
warnings.filterwarnings("ignore", message=".*there are non-text parts in the response.*", category=UserWarning)

# Suppress Google GenAI warnings by setting its logger to ERROR level
logging.getLogger("google_genai.models").setLevel(logging.ERROR)

class AgentExecutor(AgentExecutor):
    """Test AgentProxy Implementation."""
    def __init__(self):
        logger.info("Initializing AgentExecutor")
        self.agent_logger = AgentLogger("MechanicsAgent")
        self.agent = MechanicsAgent()
        
        # Log agent configuration at executor level
        logger.info(f"🚀 AGENT EXECUTOR INITIALIZED:")
        logger.info(f"   Agent Name: {getattr(self.agent.agent, 'name', 'NOT SET')}")
        logger.info(f"   Agent Description: {getattr(self.agent.agent, 'description', 'NOT SET')}")
        logger.info(f"   Agent Instruction: {getattr(self.agent.agent, 'instruction', 'NOT SET')}")

    @override
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Extract message text
        message_text = None
        if hasattr(context.message, "parts") and context.message.parts:
            message_text = "".join(
                part.root.text for part in context.message.parts if hasattr(part, "root") and hasattr(part.root, "text")
            )

        if not message_text:
            raise Exception("No message found in request context")

        # Metadata (fall back if missing)
        user_id = context.metadata.get("user_id") if context.metadata else str(uuid.uuid4())
        server_id = context.metadata.get("server_id") if context.metadata else "default-server"
        
        # Convert message to Content format and include context metadata
        enhanced_message = f"""[CONTEXT]
            user_id: {user_id}
            server_id: {server_id}

            [USER REQUEST]
            {message_text}"""

        # Always create a new session to avoid "Session not found" errors
        session = await self.agent.runner.session_service.create_session(
            app_name=self.agent.runner.app_name,
            user_id=user_id,
        )
        session_id = session.id
        self.agent_logger.start_execution(user_id, session_id, enhanced_message)

        # 🔑 Now run the agent within that session
        # Convert message to Content format (same as agent.py invoke method)
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=enhanced_message)],
        )
        
        final_text = None

        async for event in self.agent.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            # capture text from ADK events
            if getattr(event, "text", None):
                self.agent_logger.log_step(event.author, "Response: " + event.text)
                final_text = event.text
            elif getattr(event, "content", None) and getattr(event.content, "parts", None):
                # pick the last non-empty text part as final
                texts = [getattr(p, "text", None) for p in event.content.parts if getattr(p, "text", None)]
                if texts:
                    final_text = texts[-1]
                    self.agent_logger.log_step(event.author, "Response: " + final_text)

            # DO NOT enqueue raw ADK events to A2A; they’re not A2A events

        # after the loop, send an actual A2A message event:
        await event_queue.enqueue_event(
            new_agent_text_message(final_text or "Done.")
        )

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported") 
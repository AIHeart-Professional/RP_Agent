from typing_extensions import override
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from agent import VeritasAgent
from google.genai import types
import uuid
import logging
import warnings
from config.logging_config import setup_logging
from utils.agent_display import AgentLogger

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
        self.agent_logger = AgentLogger("VeritasAgent")
        self.agent = VeritasAgent()

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
        
        # Always create a new session to avoid "Session not found" errors
        session = await self.agent.session.create_session(
            app_name=self.agent.runner.app_name,
            user_id=user_id,
        )
        session_id = session.id
        self.agent_logger.start_execution(user_id, session_id, message_text)

        # 🔑 Now run the agent within that session
        # Convert message to Content format and include context metadata
        enhanced_message = f"""[CONTEXT]
            user_id: {user_id}
            server_id: {server_id}

            [USER REQUEST]
            {message_text}"""
        
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=enhanced_message)],
        )
        
        event_count = 0
        self.agent_logger.log_step("VeritasAgent", f"🎯 Starting agent execution with session {session_id}")
        
        final_text = None

        async for event in self.agent.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            # ... your existing logging ...
            if getattr(event, "text", None):
                self.agent_logger.log_step(event.author, "Text: " + event.text)
                final_text = event.text
            elif getattr(event, "content", None) and getattr(event.content, "parts", None):
                texts = [getattr(p, "text", None) for p in event.content.parts if getattr(p, "text", None)]
                if texts:
                    final_text = texts[-1]
                    self.agent_logger.log_step(event.author, "Text: " + final_text)

            # ❌ remove this:
            # await event_queue.enqueue_event(event)

        # ✅ send a proper A2A agent message so the handler doesn’t 500:
        await event_queue.enqueue_event(new_agent_text_message(final_text or "Done."))
    
    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported") 
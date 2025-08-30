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
        # Convert message to Content format (same as agent.py invoke method)
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=message_text)],
        )
        
        event_count = 0
        self.agent_logger.log_step("VeritasAgent", f"🎯 Starting agent execution with session {session_id}")
        
        async for event in self.agent.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            event_count += 1
            
            # Log different types of events for debugging
            event_type = type(event).__name__
            self.agent_logger.log_step("VeritasAgent", f"📡 Event #{event_count}: {event_type}")
            
            # Log specific event details
            if hasattr(event, 'text') and event.text:
                self.agent_logger.log_step("VeritasAgent", f"💬 Agent Response: {event.text[:200]}{'...' if len(event.text) > 200 else ''}")
            elif hasattr(event, 'content'):
                if hasattr(event.content, 'parts'):
                    for i, part in enumerate(event.content.parts):
                        if hasattr(part, 'text') and part.text:
                            self.agent_logger.log_step("VeritasAgent", f"💬 Agent Response Part {i+1}: {part.text[:200]}{'...' if len(part.text) > 200 else ''}")
                        elif hasattr(part, 'function_call'):
                            func_call = part.function_call
                            func_name = getattr(func_call, 'name', 'Unknown') if func_call else 'Unknown'
                            func_args = getattr(func_call, 'args', {}) if func_call else {}
                        #    logger.info(f"🔧 Function Call: {func_name} | Args: {str(func_args)[:100]}{'...' if len(str(func_args)) > 100 else ''}")
                        elif hasattr(part, 'function_response'):
                            func_resp = part.function_response
                            func_name = getattr(func_resp, 'name', 'Unknown') if func_resp else 'Unknown'
                            func_result = getattr(func_resp, 'response', getattr(func_resp, 'result', 'No result')) if func_resp else 'No result'
                        #    logger.info(f"🔄 Function Response: {func_name} | Result: {str(func_result)[:100]}{'...' if len(str(func_result)) > 100 else ''}")
                else:
                    self.agent_logger.log_step("VeritasAgent", "📄 Event Content: ")
            
            await event_queue.enqueue_event(event)
        
        self.agent_logger.log_step("VeritasAgent", f"✅ VERITAS AGENT COMPLETED - Processed {event_count} events for session {session_id}")

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported") 
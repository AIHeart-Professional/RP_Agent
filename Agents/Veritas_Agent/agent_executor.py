from typing_extensions import override
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from agent import VeritasAgent
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
        # Extract message text from the request context
        message_text = context.message.parts[0].root.text
        # Extract user_id and server_id from context
        user_id = None
        server_id = None
        session_id = None
        # Also check context metadata as fallback
        if context.metadata:
            logger.info(f"Checking context metadata: {context.metadata}")
            user_id = context.metadata.get('user_id')
            if user_id is None:
                logger.info("No user_id found")
                raise Exception("No user_id found")
            server_id = context.metadata.get('server_id')
            if server_id is None:
                logger.info("No server_id found")
                raise Exception("No server_id found")
            session_id = context.metadata.get('session_id')
            if session_id is None:
                logger.info("No session_id found: Creating sesion")
                session_id = str(uuid.uuid4())        
        if hasattr(context, 'message') and context.message:
            if hasattr(context.message, 'parts') and context.message.parts:
                for part in context.message.parts:
                    if hasattr(part, 'text'):
                        message_text += part.text
        
        # If no message found, use a default
        if not message_text:
            raise Exception("No message found in request context")
        
        # Invoke agent with the actual message and context
        self.agent_logger.start_execution(user_id, session_id, message_text)
        result = await self.agent.invoke(message_text, user_id=user_id, server_id=server_id)
        await event_queue.enqueue_event(new_agent_text_message(result))

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported") 
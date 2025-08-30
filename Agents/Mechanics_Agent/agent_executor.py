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
        
        # Retrieve context before creating session (if available)
        enhanced_message = message_text
        if CONTEXT_AVAILABLE and context_manager:
            try:
                # Get relevant conversation history
                conversation_context = await context_manager.retrieve_relevant_context(
                    user_id=user_id, 
                    query=message_text, 
                    max_chunks=3, 
                    max_tokens=1000
                )
                
                # Get persona context for character consistency
                persona_context = await context_manager.get_persona_context(user_id)
                
                # Enhance message with context
                if conversation_context or persona_context:
                    context_parts = []
                    if conversation_context:
                        context_parts.append(f"[CONVERSATION HISTORY]\n{conversation_context}")
                    if persona_context:
                        context_parts.append(f"[CHARACTER CONTEXT]\n{persona_context}")
                    
                    enhanced_message = f"{chr(10).join(context_parts)}\n\n[CURRENT MESSAGE]\n{message_text}"
                    logger.info(f"Enhanced message with context for user {user_id}")
                
            except Exception as e:
                logger.warning(f"Failed to retrieve context: {e}, proceeding without context")
                enhanced_message = message_text
        else:
            logger.info(f"Context manager not available, using original message for user {user_id}")
        
        # Always create a new session to avoid "Session not found" errors
        session = await self.agent.session.create_session(
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
        
        event_count = 0
        logger.info(f"🎯 Starting agent execution with session {session_id}")
        
        async for event in self.agent.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            event_count += 1
            
            # Log different types of events for debugging
            self.agent_logger.log_step(event.author, message_text)
            # Log specific event details
            if hasattr(event, 'text') and event.text:
                self.agent_logger.log_step(event.author, f"💬 Agent Response: {event.text[:200]}{'...' if len(event.text) > 200 else ''}")
            elif hasattr(event, 'content'):
                if hasattr(event.content, 'parts'):
                    for i, part in enumerate(event.content.parts):
                        if hasattr(part, 'text') and part.text:
                            self.agent_logger.log_step(event.author, f"💬 Agent Response Part {i+1}: {part.text[:200]}{'...' if len(part.text) > 200 else ''}")
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
                    self.agent_logger.log_step(event.author, "📄 Event Content: ")
            
            await event_queue.enqueue_event(event)
        
        self.agent_logger.log_step(event.author, f"✅ MECHANICS AGENT COMPLETED - Processed {event_count} events for session {session_id}")

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported") 
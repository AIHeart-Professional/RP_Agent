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
        # Step 0: Initialize variables
        message_text = None
        stream = False
        user_id = ""
        server_id = ""
        
        # Step 1: If there is a previous agent response.
        if hasattr(context.message, "parts") and context.message.parts:
            # Step 1a: Extract message string from previous agent response
            message_text = "".join(
                part.root.text for part in context.message.parts if hasattr(part, "root") and hasattr(part.root, "text")
            )
        # Step 2: If there is no previous agent response.
        if not message_text:
            raise Exception("No message found in request context")
        # Step 3: Extract user_id and server_id from request context
        user_id = context.metadata.get("user_id") if context.metadata else str(uuid.uuid4())
        server_id = context.metadata.get("server_id") if context.metadata else "default-server"
        
        # Step 4: Convert message to string holding required fields and previous agent responses
        enhanced_message = f"""[CONTEXT]
            user_id: {user_id}
            server_id: {server_id}

            [USER REQUEST]
            {message_text}"""

        # Step 5: Create a new session
        session = await self.agent.runner.session_service.create_session(
            app_name=self.agent.runner.app_name,
            user_id=user_id,
        )
        session_id = session.id
        self.agent_logger.start_execution(user_id, session_id, enhanced_message)

        # Step 6: Convert message to A2A format
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=enhanced_message)],
        )
        
        final_text = None

        # Step 7: Run the agent and process events
        async for event in self.agent.runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            # 7a: capture responses from ADK events
            if getattr(event, "text", None):
                self.agent_logger.log_step(event.author, "Response: " + event.text)
                final_text = event.text
                
                # Optional: Send intermediate streaming response
                if stream:
                    await event_queue.enqueue_event(
                        new_agent_text_message(event.text)
                    )
                    
            elif getattr(event, "content", None) and getattr(event.content, "parts", None):
                # 7b: Process all parts including function calls
                for part in event.content.parts:
                    if getattr(part, "text", None):
                        final_text = part.text
                        self.agent_logger.log_step(event.author, "Text: " + part.text)
                        
                        # Optional: Send intermediate streaming response
                        if stream:
                            await event_queue.enqueue_event(
                                new_agent_text_message(part.text)
                            )
                    elif getattr(part, "function_call", None):
                        # Log function call but don't try to execute it - ADK handles this
                        func_call = part.function_call
                        self.agent_logger.log_step(event.author, f"Function Call: {func_call.name}")
                    elif getattr(part, "function_response", None):
                        # Log function response
                        func_response = part.function_response
                        self.agent_logger.log_step(event.author, f"Function Response: {func_response.name}")
                        
                # Fallback: get text from all text parts
                texts = [getattr(p, "text", None) for p in event.content.parts if getattr(p, "text", None)]
                if texts and not final_text:
                    final_text = " ".join(texts)
                    self.agent_logger.log_step(event.author, "Combined Text: " + final_text)
            
            # Check if this is the final response using ADK's built-in method
            if hasattr(event, 'is_final_response') and event.is_final_response():
                self.agent_logger.log_step("System", "Final response received")
                break

        # Step 8: Enqueue final response
        await event_queue.enqueue_event(
            new_agent_text_message(final_text or "Done.")
        )

    @override
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported") 
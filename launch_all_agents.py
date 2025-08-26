#!/usr/bin/env python3
"""
Master launcher script for all A2A agents.
This script can be used with VS Code debugger to launch and debug all agents simultaneously.
"""

import asyncio
import multiprocessing
import os
import sys
import time
import uvicorn
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def start_veritas_agent():
    """Start the Veritas Agent on port 9999"""
    os.chdir(PROJECT_ROOT / "Agents" / "Veritas_Agent")
    sys.path.insert(0, str(PROJECT_ROOT / "Agents" / "Veritas_Agent"))
    
    from agent_executor import AgentExecutor
    from agent_card import agent_card
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.tasks import InMemoryTaskStore
    
    print("🚀 Starting Veritas Agent on port 9999...")
    
    # 1. Request Handler
    request_handler = DefaultRequestHandler(
        agent_executor=AgentExecutor(),
        task_store=InMemoryTaskStore()
    )

    # 2. Starlette Application
    server_app_builder = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

    app = server_app_builder.build()
    print("✅ Veritas Agent routes registered")
    
    # 3. Start Server
    uvicorn.run(app, host='0.0.0.0', port=9999, log_level="info")

def start_mechanics_agent():
    """Start the Mechanics Agent on port 9998"""
    os.chdir(PROJECT_ROOT / "Agents" / "Mechanics_Agent")
    sys.path.insert(0, str(PROJECT_ROOT / "Agents" / "Mechanics_Agent"))
    
    from agent_executor import AgentExecutor
    from agent_card import agent_card
    from a2a.server.apps import A2AStarletteApplication
    from a2a.server.request_handlers import DefaultRequestHandler
    from a2a.server.tasks import InMemoryTaskStore
    
    print("🚀 Starting Mechanics Agent on port 9998...")
    
    # 1. Request Handler
    request_handler = DefaultRequestHandler(
        agent_executor=AgentExecutor(),
        task_store=InMemoryTaskStore()
    )

    # 2. Starlette Application
    server_app_builder = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

    app = server_app_builder.build()
    print("✅ Mechanics Agent routes registered")
    
    # 3. Start Server
    uvicorn.run(app, host='0.0.0.0', port=9998, log_level="info")

async def main():
    """Main function to coordinate all agent startups"""
    print("🌟 A2A Agent Orchestrator Starting...")
    print("=" * 50)
    
    # Create processes for each agent
    processes = []
    
    # Start Veritas Agent
    veritas_process = multiprocessing.Process(target=start_veritas_agent, name="VeritasAgent")
    processes.append(veritas_process)
    
    # Start Mechanics Agent  
    mechanics_process = multiprocessing.Process(target=start_mechanics_agent, name="MechanicsAgent")
    processes.append(mechanics_process)
        
    # Start all processes
    for process in processes:
        process.start()
        print(f"✅ Started {process.name} (PID: {process.pid})")
        time.sleep(1)  # Small delay between starts
    
    print("=" * 50)
    print("🎉 All agents started successfully!")
    print("📍 Agent URLs:")
    print("   • Veritas Agent:  http://localhost:9999")
    print("   • Mechanics Agent: http://localhost:9998") 
    print("=" * 50)
    print("Press Ctrl+C to stop all agents...")
    
    try:
        # Wait for all processes
        for process in processes:
            process.join()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down all agents...")
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
        print("✅ All agents stopped.")

if __name__ == "__main__":
    # Handle multiprocessing on Windows
    multiprocessing.set_start_method('spawn', force=True)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

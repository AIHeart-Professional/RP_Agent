#!/usr/bin/env python3
"""
Narrative Agent A2A Server
Runs the narrative agent as an A2A server on port 9998
"""
import uvicorn
import logging
from .agent import create_app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Run the narrative agent server"""
    app = create_app()
    logger.info("Starting Narrative Agent A2A server on port 9998...")
    uvicorn.run(app, host="0.0.0.0", port=9998)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Test script to verify logging configuration works properly."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.logging_config import setup_logging
import logging

def test_logging():
    """Test the logging configuration."""
    print("Testing logging configuration...")
    
    # Setup logging
    setup_logging()
    
    # Get logger
    logger = logging.getLogger(__name__)
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test agent logger
    agent_logger = logging.getLogger('agent')
    agent_logger.info("Agent logger test message")
    
    print("Logging test completed. Check logs/app.log for file output.")

if __name__ == "__main__":
    test_logging()

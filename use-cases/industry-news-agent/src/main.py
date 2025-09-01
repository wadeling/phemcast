#!/usr/bin/env python3
"""Main entry point for the industry news agent application."""
import asyncio
import multiprocessing
import signal
import sys
import os
from pathlib import Path

# Import from current directory (src)
import sys
import os

# Add current directory to Python path for absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Use absolute imports
try:
    from settings import load_settings
    from logging_config import setup_logging, get_logger
    from task_processor import TaskProcessor
except ImportError as e:
    print(f"Import error: {e}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print(f"Files in current directory: {os.listdir('.')}")
    raise

# Global variables for graceful shutdown
fastapi_process = None
task_processor_process = None
shutdown_event = multiprocessing.Event()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger = get_logger(__name__)
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()
    
    # Stop task processor
    if task_processor_process is not None and task_processor_process.is_alive():
        try:
            logger.info("Terminating task processor process...")
            task_processor_process.terminate()
            task_processor_process.join(timeout=5)
            if task_processor_process.is_alive():
                logger.warning("Task processor process did not terminate gracefully, killing...")
                task_processor_process.kill()
            logger.info("Task processor process stopped")
        except Exception as e:
            logger.error(f"Error stopping task processor process: {e}")
    
    # Stop FastAPI
    if fastapi_process is not None and fastapi_process.is_alive():
        try:
            logger.info("Terminating FastAPI process...")
            fastapi_process.terminate()
            fastapi_process.join(timeout=5)
            if fastapi_process.is_alive():
                logger.warning("FastAPI process did not terminate gracefully, killing...")
                fastapi_process.kill()
            logger.info("FastAPI process stopped")
        except Exception as e:
            logger.error(f"Error stopping FastAPI process: {e}")
    
    logger.info("Shutdown completed.")
    sys.exit(0)

def start_fastapi():
    """Start the FastAPI web server."""
    import uvicorn
    from web_interface import app
    
    # Load settings
    settings = load_settings()
    
    # Setup logging
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file,
        show_file_line=settings.show_file_line,
        show_function=settings.show_function
    )
    
    logger = get_logger(__name__)
    logger.info("Starting FastAPI web server...")
    
    try:
        # Start FastAPI server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level=str(settings.uvicorn_log_level).lower(),  # Ensure string type and lowercase
            access_log=True,
            # Additional logging control
            log_config=None  # Use default logging to avoid conflicts
        )
    except Exception as e:
        logger.error(f"Failed to start FastAPI server: {e}")
        import traceback
        logger.error(f"FastAPI error traceback: {traceback.format_exc()}")
        raise

def start_task_processor():
    """Start the background task processor."""
    # Load settings
    settings = load_settings()
    
    # Setup logging
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file,
        show_file_line=settings.show_file_line,
        show_function=settings.show_function
    )
    
    logger = get_logger(__name__)
    logger.info("Starting background task processor...")
    
    # Create and start task processor
    from task_processor import TaskProcessor
    processor = TaskProcessor()
    asyncio.run(processor.run())

def main():
    """Main function to start both FastAPI and task processor."""
    global fastapi_process, task_processor_process
    
    # Initialize process variables
    fastapi_process = None
    task_processor_process = None
    
    # Load settings
    settings = load_settings()
    
    # Setup logging
    setup_logging(
        log_level=settings.log_level,
        log_file=settings.log_file,
        show_file_line=settings.show_file_line,
        show_function=settings.show_function
    )
    
    logger = get_logger(__name__)
    logger.info("Starting Industry News Agent application...")
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start task processor in a separate process
        logger.info("Starting background task processor...")
        task_processor_process = multiprocessing.Process(
            target=start_task_processor,
            name="TaskProcessor"
        )
        task_processor_process.start()
        logger.info(f"Task processor process started with PID: {task_processor_process.pid}")
        
        # Start FastAPI in the main process
        logger.info("Starting FastAPI web server...")
        start_fastapi()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        import traceback
        logger.error(f"Error traceback: {traceback.format_exc()}")
        if task_processor_process is not None:
            signal_handler(signal.SIGTERM, None)
        sys.exit(1)

if __name__ == "__main__":
    # Set multiprocessing start method for macOS compatibility
    if sys.platform == "darwin":
        multiprocessing.set_start_method('spawn')
    
    main()

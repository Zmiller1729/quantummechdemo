import abc
import asyncio
import os
import json
import argparse
import openai
import base64
import time
import websockets
import logging  # <-- Add this import
from datetime import datetime
from websockets.exceptions import ConnectionClosedError
from dotenv import load_dotenv
from src.modules.logging import log_error, log_info, log_warning, log_ws_event, log_tool_call, setup_logging
from src.modules.async_microphone import AsyncMicrophone
from src.modules.audio import play_audio
from src.modules.tools.base import function_map, tools
from src.modules.utils import (
    RUN_TIME_TABLE_LOG_JSON,
    SESSION_INSTRUCTIONS,
    PREFIX_PADDING_MS,
    SILENCE_THRESHOLD,
    SILENCE_DURATION_MS,
)
import sys

class AssistantAPI(metaclass=abc.ABCMeta):
    """Base class for assistant implementations."""
    
    def __init__(self, prompts=None, debug=False):
        self.prompts = prompts
        self.api_key = self.get_api_key()
        self.exit_event = asyncio.Event()
        self.mic = AsyncMicrophone()

        # Initialize state variables
        self.logger = self.setup_logging("assistant", debug)
        self.assistant_reply = ""
        self.audio_chunks = []
        self.response_in_progress = False
        self.function_call = None
        self.function_call_args = ""
        self.response_start_time = None


    def base64_encode_audio(self, audio_bytes):
        return base64.b64encode(audio_bytes).decode("utf-8")


    def log_runtime(self, function_or_name: str, duration: float):
        jsonl_file = RUN_TIME_TABLE_LOG_JSON
        time_record = {
            "timestamp": datetime.now().isoformat(),
            "function": function_or_name,
            "duration": f"{duration:.4f}",
        }
        with open(jsonl_file, "a") as file:
            json.dump(time_record, file)
            file.write("\n")

        self.logger.info(f"⏰ {function_or_name}() took {duration:.4f} seconds")


    def get_api_key(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.logger.error("Please set the OPENAI_API_KEY in your .env file.")
            sys.exit(1)
        return api_key

    def setup_logging(self, logger_name, debug):
        """
        Set up logging for the assistant.

        Args:
            logger_name (str): The name of the logger.
            debug (bool): Whether to enable debug logging.

        Returns:
            logging.Logger: The configured logger instance.
        """
        level = logging.DEBUG if debug else logging.INFO
        return setup_logging(logger_name, level)
    async def run(self):
        """Main execution loop for the assistant."""
        pass


    @abc.abstractmethod
    async def initialize_session(self, websocket=None):
        """Initialize the assistant session."""
        pass

    @abc.abstractmethod
    async def send_initial_prompts(self, websocket=None):
        """Send initial prompts to the assistant."""
        pass

    @abc.abstractmethod
    async def handle_event(self, event, websocket=None):
        """Handle incoming events."""
        pass

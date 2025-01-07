import logging
import sys
from rich.logging import RichHandler
from rich.console import Console
from rich.text import Text

console = Console()

def setup_logging(logger_name="assistant", level=logging.INFO):
    """
    Set up logging with Rich for the given logger name and level.
    
    Args:
        logger_name (str): The name of the logger.
        level (int): The logging level (e.g., logging.INFO, logging.DEBUG).
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Set up RichHandler for pretty logging
    handler = RichHandler(rich_tracebacks=True, console=console)
    formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    handler.setFormatter(formatter)
    
    # Add handler to the logger
    logger.addHandler(handler)
    logger.propagate = False
    return logger

def log_ws_event(logger, direction, event):
    """
    Log WebSocket events with appropriate emojis and styles.
    
    Args:
        logger (logging.Logger): The logger instance.
        direction (str): "Incoming" or "Outgoing".
        event (dict): The WebSocket event data.
    """
    if not logger.isEnabledFor(logging.DEBUG):
        return
        
    event_type = event.get("type", "Unknown")
    event_emojis = {
        "session.update": "🛠️",
        "session.created": "🔌",
        "session.updated": "🔄",
        "input_audio_buffer.append": "🎤",
        "input_audio_buffer.commit": "✅",
        "input_audio_buffer.speech_started": "🗣️",
        "input_audio_buffer.speech_stopped": "🤫",
        "input_audio_buffer.cleared": "🧹",
        "input_audio_buffer.committed": "📨",
        "conversation.item.create": "📥",
        "conversation.item.delete": "🗑️",
        "conversation.item.truncate": "✂️",
        "conversation.item.created": "📤",
        "conversation.item.deleted": "🗑️",
        "conversation.item.truncated": "✂️",
        "response.create": "➡️",
        "response.created": "📝",
        "response.output_item.added": "➕",
        "response.output_item.done": "✅",
        "response.text.delta": "✍️",
        "response.text.done": "📝",
        "response.audio.delta": "🔊",
        "response.audio.done": "🔇",
        "response.done": "✔️",
        "response.cancel": "⛔",
        "response.function_call_arguments.delta": "📥",
        "response.function_call_arguments.done": "📥",
        "rate_limits.updated": "⏳",
        "error": "❌",
        "conversation.item.input_audio_transcription.completed": "📝",
        "conversation.item.input_audio_transcription.failed": "⚠️",
    }
    emoji = event_emojis.get(event_type, "❓")
    icon = "⬆️ - Out" if direction == "Outgoing" else "⬇️ - In"
    style = "bold cyan" if direction == "Outgoing" else "bold green"
    logger.info(Text(f"{emoji} {icon} {event_type}", style=style))

def log_tool_call(logger, function_name, args, result):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(Text(f"🛠️ Calling function: {function_name} with args: {args}", style="bold magenta"))
        logger.debug(Text(f"🛠️ Function call result: {result}", style="bold yellow"))

def log_error(logger, message):
    if logger.isEnabledFor(logging.ERROR):
        logger.error(Text(message, style="bold red"))

def log_info(logger, message, style="bold white"):
    if logger.isEnabledFor(logging.INFO):
        logger.info(Text(message, style=style))

def log_warning(logger, message):
    if logger.isEnabledFor(logging.WARNING):
        logger.warning(Text(message, style="bold yellow"))

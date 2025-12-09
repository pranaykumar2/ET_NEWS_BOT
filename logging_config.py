import logging
import sys
import traceback
import pytz
from datetime import datetime
from telegram.error import NetworkError, TelegramError
from httpx import ConnectError, ReadTimeout, ConnectTimeout

# Custom Colors
class Colors:
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GREY = "\033[90m"

# 1. Custom Concise Formatter for Console
class ConciseConsoleFormatter(logging.Formatter):
    """
    Formats logs for the console:
    - INFO: Green Check / Info Icon + Message
    - WARNING: Yellow Triangle + Message
    - ERROR: Red Cross + Short Message (No Traceback)
    """
    def format(self, record):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if record.levelno == logging.INFO:
            if "Sent:" in record.msg:
                icon = f"{Colors.GREEN}✅{Colors.RESET}"
            elif "Processing:" in record.msg or "Queued" in record.msg:
                icon = f"{Colors.BLUE}ℹ️{Colors.RESET}"
            else:
                icon = f"{Colors.BLUE}🔹{Colors.RESET}"
            
            return f"{Colors.GREY}[{timestamp}]{Colors.RESET} {icon} {record.msg}"
        
        elif record.levelno == logging.WARNING:
            return f"{Colors.GREY}[{timestamp}]{Colors.RESET} {Colors.YELLOW}⚠️  {record.msg}{Colors.RESET}"
        
        elif record.levelno == logging.ERROR:
            # Strip traceback for console, just show the message
            return f"{Colors.GREY}[{timestamp}]{Colors.RESET} {Colors.RED}❌ {record.msg}{Colors.RESET}"
        
        elif record.levelno == logging.DEBUG:
            return f"{Colors.GREY}[{timestamp}] 🐛 {record.msg}{Colors.RESET}"
        
        return super().format(record)

# 2. Detailed Formatter for Files (with IST support)
class ISTFormatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp, pytz.timezone('Asia/Kolkata'))
        return dt.timetuple()

def setup_logging():
    """Configures the logging system"""
    
    # Root Logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()

    # --- Console Handler (Concise, User Friendly) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ConciseConsoleFormatter())
    
    # Filter out noisy libraries from console
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("httpcore").setLevel(logging.ERROR)
    logging.getLogger("telegram").setLevel(logging.ERROR)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    # --- File Handler (Clean History) ---
    file_handler = logging.FileHandler('news_bot.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(ISTFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S'))

    # --- Debug File Handler (Full Tracebacks) ---
    debug_handler = logging.FileHandler('news_bot_debug.log', encoding='utf-8')
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(ISTFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(exc_text)s', '%Y-%m-%d %H:%M:%S'))

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(debug_handler)
    
    return logger

async def error_handler(update, context):
    """
    Custom error handler to trap exceptions and log them nicely.
    """
    logger = logging.getLogger(__name__)
    
    try:
        raise context.error
    except (NetworkError, ConnectError, ReadTimeout, ConnectTimeout) as e:
        # Network issues - One liner in console
        logger.warning(f"Network Connection Lost: {e}. Retrying implicitly...")
        # Full traceback only in debug file (handled by logger automatically if we use exc_info=False for warning, but we want it in debug)
        # We manually log to debug for the traceback
        logging.getLogger('debug_logger').debug(f"Network Error Detail", exc_info=context.error)
        
    except TelegramError as e:
        logger.error(f"Telegram API Error: {e}")
        
    except Exception as e:
        # Unexpected fatal errors
        logger.error(f"Unexpected Error: {e}. Check debug log.")
        logging.getLogger('debug_logger').debug(f"Critical Error", exc_info=context.error)

# Helper to log exceptions properly from anywhere
def log_exception(e: Exception, message: str = "An error occurred"):
    logger = logging.getLogger(__name__)
    logger.error(f"{message}: {str(e)}")
    
    # Write full traceback to debug file manually if needed, 
    # but the Debug Handler on root logger will catch 'error' level logs. 
    # However, 'error' logs in console don't show traceback due to custom formatter.
    # The 'debug_handler' uses a formatter that INCLUDES %(exc_text)s, so we must pass exc_info=True.
    
    # We want:
    # Console: "❌ An error occurred: Division by zero"
    # File (Info): "ERROR - An error occurred: Division by zero"
    # File (Debug): "ERROR ... \n Traceback ..."
    
    # To achieve this, we can't just pass exc_info=True because the Console Formatter would need to explicitly IGNORE it, 
    # which it does by not including %(exc_text)s, BUT the StreamHandler might print it anyway if passed?
    # No, StreamHandler uses the formatter. If formatter doesn't format exception, it might be appended?
    # Standard logging behavior: if exc_info is present, it formats it.
    
    # So we need to be careful.
    # Approach: Log the message as ERROR (for console/file).
    # Log the traceback as DEBUG (for debug file).
    
    logger.debug(f"Traceback for: {message}", exc_info=e)

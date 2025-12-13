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
    RED = "\033[38;2;255;95;87m"        # Soft Red
    GREEN = "\033[38;2;40;200;64m"      # Fresh Green
    YELLOW = "\033[38;2;255;211;7m"     # Bright Yellow
    BLUE = "\033[38;2;0;122;255m"       # Azure Blue
    PURPLE = "\033[38;2;175;82;222m"    # Purple
    CYAN = "\033[38;2;88;86;214m"       # Indigo/Cyan
    GREY = "\033[38;2;142;142;147m"     # Slate Grey
    WHITE = "\033[38;2;255;255;255m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

class LogStyler:
    """Helper for drawing boxes and tables"""
    @staticmethod
    def box(title: str, lines: list, color=Colors.BLUE):
        width = 50
        print(f"{color}╭" + "─" * (width - 2) + "╮" + Colors.RESET)
        
        # Title
        pad_len = (width - 4 - len(title)) // 2
        print(f"{color}│{Colors.RESET} {Colors.BOLD}{' ' * pad_len}{title}{' ' * (width - 4 - len(title) - pad_len)} {color}│{Colors.RESET}")
        
        print(f"{color}├" + "─" * (width - 2) + "┤" + Colors.RESET)
        
        for line in lines:
            # Handle key-value pairs or plain strings
            if isinstance(line, tuple):
                key, val = line
                content = f"{key:<15} {val}"
            else:
                content = line
            
            # Simple truncation/padding logic
            # (In a real CLI app, we'd measure visible length properly)
            text_len = len(str(content).replace(Colors.RESET, "").replace(Colors.GREEN, "")) # Very approximate
            if text_len > width - 4:
                content = content[:width-7] + "..."
                
            padding = width - 4 - len(str(content).replace(Colors.RESET, "").replace(Colors.GREEN, "").replace(Colors.BLUE, "").replace(Colors.YELLOW, "").replace(Colors.RED, ""))
            # Using max to avoid negative padding
            padding = max(0, padding)
            
            print(f"{color}│{Colors.RESET} {content}{' ' * padding} {color}│{Colors.RESET}")
            
        print(f"{color}╰" + "─" * (width - 2) + "╯" + Colors.RESET)

# 1. Modern Formatter for Console
class ModernConsoleFormatter(logging.Formatter):
    """
    Formats logs with a structured, columnar look.
    """
    def format(self, record):
        timestamp = datetime.now().strftime("%H:%M:%S")
        ts_block = f"{Colors.GREY}[{timestamp}]{Colors.RESET}"
        
        message = record.msg
        
        # Categorize Logs for Visual tagging
        if record.levelno == logging.INFO:
            if "Sent:" in message or "✅" in message:
                tag = f"{Colors.GREEN} SENT {Colors.RESET}"
                # Indent success message slightly for flow
                if "Sent:" in message:
                    message = f"   ╰──> {message}"
                    
            elif "Processing:" in message or "Worker" in message:
                tag = f"{Colors.YELLOW} WORK {Colors.RESET}"
                
            elif "Queued" in message or "Scan" in message:
                tag = f"{Colors.PURPLE} FEED {Colors.RESET}"
                
            else:
                tag = f"{Colors.BLUE} INFO {Colors.RESET}"
                
        elif record.levelno == logging.WARNING:
            tag = f"{Colors.YELLOW} WARN {Colors.RESET}"
            message = f"{Colors.YELLOW}{message}{Colors.RESET}"
            
        elif record.levelno == logging.ERROR:
            tag = f"{Colors.RED} ERR  {Colors.RESET}"
            message = f"{Colors.RED}{message}{Colors.RESET}"
            
        elif record.levelno == logging.DEBUG:
            tag = f"{Colors.GREY} DEBG {Colors.RESET}"
        
        else:
            tag = "      "

        return f"{ts_block} ▕{tag}▏ {message}"

# 2. Detailed Formatter for Files (with IST support) - Unchanged
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

    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ModernConsoleFormatter())
    
    # Filter out noisy libraries
    logging.getLogger("httpx").setLevel(logging.ERROR)
    logging.getLogger("httpcore").setLevel(logging.ERROR)
    logging.getLogger("telegram").setLevel(logging.ERROR)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    # --- File Handler ---
    file_handler = logging.FileHandler('news_bot.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(ISTFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S'))

    # --- Debug File Handler ---
    debug_handler = logging.FileHandler('news_bot_debug.log', encoding='utf-8')
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(ISTFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(exc_text)s', '%Y-%m-%d %H:%M:%S'))

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(debug_handler)
    
    return logger

async def error_handler(update, context):
    logger = logging.getLogger(__name__)
    try:
        raise context.error
    except (NetworkError, ConnectError, ReadTimeout, ConnectTimeout) as e:
        logger.warning(f"Network Connection Lost: {e}. Retrying implicitly...")
        logging.getLogger('debug_logger').debug(f"Network Error Detail", exc_info=context.error)
    except TelegramError as e:
        logger.error(f"Telegram API Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        logging.getLogger('debug_logger').debug(f"Critical Error", exc_info=context.error)

def log_exception(e: Exception, message: str = "An error occurred"):
    logger = logging.getLogger(__name__)
    logger.error(f"{message}: {str(e)}")
    logger.debug(f"Traceback for: {message}", exc_info=e)

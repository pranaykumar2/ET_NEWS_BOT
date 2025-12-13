"""
Configuration loader - reads from .env file and provides RSS feed configuration
"""
import os
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'your_bot_token_here')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID', '@your_channel_name')
IV_RHASH = os.getenv('IV_RHASH', '') # Instant View RHash
DATABASE_PATH = os.getenv('DATABASE_PATH', 'news_tracker.db')
CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', '5'))
MAX_ARTICLES_PER_CHECK = int(os.getenv('MAX_ARTICLES_PER_CHECK', '5'))
MIN_INTERVAL_SECONDS = int(os.getenv('MIN_INTERVAL_SECONDS', '3'))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
IMAGE_WIDTH = int(os.getenv('IMAGE_WIDTH', '1200'))
IMAGE_HEIGHT = int(os.getenv('IMAGE_HEIGHT', '630'))


# Helper function to parse RGB color from env
def parse_rgb(color_str: str, default=(0, 0, 0)) -> tuple:
    """Parse RGB color string from env (e.g., '255,0,128') to tuple (255, 0, 128)"""
    try:
        parts = color_str.split(',')
        return tuple(int(p.strip()) for p in parts)
    except:
        return default


# Image Generator Configuration Class
class Config:
    """Configuration for image generator with all customizable parameters"""
    
    # Font Sizes
    FONT_TAG_SIZE = int(os.getenv('FONT_TAG_SIZE', '38'))
    FONT_TITLE_SIZE = int(os.getenv('FONT_TITLE_SIZE', '56'))
    FONT_DESCRIPTION_SIZE = int(os.getenv('FONT_DESCRIPTION_SIZE', '44'))
    FONT_BRAND_SIZE = int(os.getenv('FONT_BRAND_SIZE', '32'))
    
    # Font Styles
    FONT_TAG_STYLE = os.getenv('FONT_TAG_STYLE', 'bold')
    FONT_TITLE_STYLE = os.getenv('FONT_TITLE_STYLE', 'bold')
    FONT_DESCRIPTION_STYLE = os.getenv('FONT_DESCRIPTION_STYLE', 'normal')
    FONT_BRAND_STYLE = os.getenv('FONT_BRAND_STYLE', 'italic')
    
    # Font Families
    FONT_TAG_FAMILY = os.getenv('FONT_TAG_FAMILY', '')
    FONT_TITLE_FAMILY = os.getenv('FONT_TITLE_FAMILY', '')
    FONT_DESCRIPTION_FAMILY = os.getenv('FONT_DESCRIPTION_FAMILY', '')
    FONT_BRAND_FAMILY = os.getenv('FONT_BRAND_FAMILY', '')
    
    # Google Fonts CSS URL
    GOOGLE_FONTS_CSS_URL = os.getenv('GOOGLE_FONTS_CSS_URL', '')
    
    # Background Colors
    BG_BLACK = parse_rgb(os.getenv('BG_BLACK', '20,20,25'))
    BG_GREY = parse_rgb(os.getenv('BG_GREY', '45,45,50'))
    CARD_BG = parse_rgb(os.getenv('CARD_BG', '255,255,255'))
    
    # Tag Colors
    TAG_BG_COLOR = parse_rgb(os.getenv('TAG_BG_COLOR', '20,20,25'))
    TAG_TEXT_COLOR = parse_rgb(os.getenv('TAG_TEXT_COLOR', '255,255,255'))
    
    # Text Colors
    TITLE_COLOR = parse_rgb(os.getenv('TITLE_COLOR', '0,51,102'))
    DESCRIPTION_COLOR = parse_rgb(os.getenv('DESCRIPTION_COLOR', '80,80,85'))
    BRAND_COLOR = parse_rgb(os.getenv('BRAND_COLOR', '20,20,25'))
    
    # Accent Colors
    SKY_BLUE = parse_rgb(os.getenv('SKY_BLUE', '87,167,255'))
    LIGHT_GREEN = parse_rgb(os.getenv('LIGHT_GREEN', '50,205,50'))

import json

# RSS Feeds Configuration
def load_feeds():
    """Load feeds from json or fallback to default."""
    try:
        with open('feeds.json', 'r') as f:
            data = json.load(f)
            return data.get('feeds', [])
    except FileNotFoundError:
        print("feeds.json not found, using default.")
    except Exception as e:
        print(f"Error loading feeds.json: {e}")
        
    return [
        {
            "name": "Stock News",
            "url": "https://economictimes.indiatimes.com/markets/stocks/news/rssfeeds/2146843.cms",
            "max_articles_per_check": MAX_ARTICLES_PER_CHECK
        }
    ]

RSS_FEEDS = load_feeds()

def get_config() -> Dict:
    """Get complete configuration"""
    return {
        'telegram_bot_token': TELEGRAM_BOT_TOKEN,
        'telegram_channel_id': TELEGRAM_CHANNEL_ID,
        'iv_rhash': IV_RHASH,
        'database_path': DATABASE_PATH,
        'check_interval_minutes': CHECK_INTERVAL_MINUTES,
        'rss_feeds': RSS_FEEDS,
        'need_picture': os.getenv("NEED_PICTURE", "YES").upper() == "YES",
        'rate_limiting': {
            'min_interval_seconds': MIN_INTERVAL_SECONDS,
            'max_retries': MAX_RETRIES
        },
        'image_settings': {
            'width': IMAGE_WIDTH,
            'height': IMAGE_HEIGHT
        }
    }

def validate_config() -> bool:
    """Validate configuration"""
    if TELEGRAM_BOT_TOKEN == 'your_bot_token_here':
        print("❌ TELEGRAM_BOT_TOKEN not set in .env file")
        return False
    
    if TELEGRAM_CHANNEL_ID == '@your_channel_name':
        print("❌ TELEGRAM_CHANNEL_ID not set in .env file")
        return False
    
    return True

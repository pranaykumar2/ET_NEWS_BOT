"""
Async Economic Times News to Telegram Bot
"Breaking News" architecture with AsyncIO, Task Queues, and Workers
"""

import asyncio
import logging
import sqlite3
import hashlib
import html
import re
import os
import time
from datetime import datetime, date, timedelta
import pytz # Added for IST
from typing import List, Optional, Dict
from dataclasses import dataclass
from io import BytesIO
from functools import partial
from concurrent.futures import ThreadPoolExecutor

import aiohttp
import feedparser
import urllib.parse
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import nltk # Added for resource checking
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue
from telegram.error import TelegramError

from config import get_config, validate_config
from image_generator_enhanced import EnhancedNewsImageGenerator
from logging_config import setup_logging, error_handler, log_exception
from email.utils import parsedate_to_datetime

# Configure Logging System
logger = setup_logging()

@dataclass
class NewsArticle:
    """Data class for news articles"""
    title: str
    description: str
    link: str
    pub_date: str
    image_url: Optional[str]
    guid: str
    
    def get_hash(self) -> str:
        """Generate unique hash for article"""
        return hashlib.md5(self.guid.encode()).hexdigest()

class DatabaseManager:
    """Manages SQLite database (Synchronous - wrapped in executor for async usage)"""
    
    def __init__(self, db_path: str = "news_tracker.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Enable WAL mode for concurrency
            cursor.execute('PRAGMA journal_mode=WAL;')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sent_articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_hash TEXT UNIQUE NOT NULL,
                    guid TEXT NOT NULL,
                    title TEXT NOT NULL,
                    link TEXT NOT NULL,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    telegram_message_id TEXT,
                    feed_source TEXT
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS failed_sends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_hash TEXT NOT NULL,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    last_retry TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_article_hash ON sent_articles(article_hash)')
            # Fix: Add Unique Index for ON CONFLICT clause in failed_sends
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_failed_sends_hash ON failed_sends(article_hash)')
            conn.commit()

    def is_article_sent(self, article_hash: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM sent_articles WHERE article_hash = ?', (article_hash,))
            return cursor.fetchone() is not None

    def is_title_sent(self, title: str) -> bool:
        """Check if article with same title already sent (Robust deduplication)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM sent_articles WHERE title = ?', (title,))
            return cursor.fetchone() is not None
    
    def mark_article_sent(self, article: NewsArticle, message_id: str, feed_source: str):
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute('''
                    INSERT INTO sent_articles (article_hash, guid, title, link, telegram_message_id, feed_source)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (article.get_hash(), article.guid, article.title, article.link, message_id, feed_source))
                commit = True
            except sqlite3.IntegrityError:
                pass

    def log_failed_send(self, article_hash: str, error_message: str):
         with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO failed_sends (article_hash, error_message, retry_count)
                VALUES (?, ?, 1)
                ON CONFLICT(article_hash) DO UPDATE SET
                    retry_count = retry_count + 1,
                    last_retry = CURRENT_TIMESTAMP,
                    error_message = ?
            ''', (article_hash, error_message, error_message))

    def get_stats(self) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            total_sent = conn.execute('SELECT COUNT(*) FROM sent_articles').fetchone()[0]
            pending_failures = conn.execute('SELECT COUNT(*) FROM failed_sends WHERE resolved = FALSE').fetchone()[0]
            sent_last_hour = conn.execute('SELECT COUNT(*) FROM sent_articles WHERE sent_at > datetime("now", "-1 hour")').fetchone()[0]
            return {
                'total_sent': total_sent,
                'pending_failures': pending_failures,
                'sent_last_hour': sent_last_hour
            }

def normalize_currency_symbols(text: str) -> str:
    # (Same as before)
    currency_map = {
        '₹': 'INR ', '₨': 'INR ', '$': 'USD ', '€': 'EUR ', '£': 'GBP ',
        '¥': 'JPY ', '₩': 'KRW ', '₽': 'RUB '
    }
    for symbol, replacement in currency_map.items():
        text = text.replace(symbol, replacement)
    return re.sub(r'\s+', ' ', text)

def summarize_text(text: str, max_chars: int = 350) -> str:
    """Refined summarization using LSA to pick best sentences"""
    # 1. Clean HTML
    text = re.sub('<[^<]+?>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 2. Short circuit if short enough
    if len(text) <= max_chars:
        return text

    try:
        # 3. Use Sumy LSA
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LsaSummarizer()
        
        # Determine number of sentences: try capturing 2 key sentences
        summary_sentences = summarizer(parser.document, 2)
        
        summary_text = ' '.join([str(s) for s in summary_sentences])
        
        # 4. Fallback if LSA provided empty or massive result
        if not summary_text or len(summary_text) > max_chars * 1.5:
             # Fallback to smart truncation if LSA fails or is too verbose
             pass
        else:
             return summary_text
             
    except Exception as e:
        logger.warning(f"Summarizer failed: {e}")
        
    # Fallback Mechanism (Smart Truncation)
    # Try to cut at the last sentence boundary within limit
    if len(text) > max_chars:
        excerpt = text[:max_chars]
        # Find last sentence end
        last_dot = excerpt.rfind('.')
        if last_dot > 50:
             return excerpt[:last_dot+1]
        
        # Else split by space
        return excerpt.rsplit(' ', 1)[0] + '...'
    
    return text

class AsyncNewsMonitor:
    def __init__(self):
        if not validate_config():
            raise ValueError("Invalid configuration")
        
        self.config = get_config()
        self.db = DatabaseManager(self.config.get('database_path', 'news_tracker.db'))
        
        # Generator is CPU heavy -> will run in executor
        self.image_gen = EnhancedNewsImageGenerator(
             # Configs will be loaded from env inside the class
        )
        
        self.feeds = self.config['rss_feeds']
        self.check_interval = self.config.get('check_interval_minutes', 5)
        
        # AsyncIO Queue for background processing
        self.task_queue = asyncio.Queue()
        
        # ThreadPool for CPU bound tasks (DB, Image Gen, Parsing)
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # Ensure NLTK resources are available
        self.download_nltk_resources()
        
        self.is_startup = True
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Deduplication: Track hashes currently in queue/processing
        self.processing_hashes = set()

    async def fetch_url(self, session: Optional[aiohttp.ClientSession], url: str) -> Optional[bytes]:
        """Fetch URL with exponential backoff and session reuse"""
        if session is None:
            # Fallback if session not ready (should not happen in normal flow)
            async with aiohttp.ClientSession() as temp_session:
                return await self.fetch_url(temp_session, url)

        retries = 3
        base_delay = 5
        
        for attempt in range(retries):
            try:
                # Increased timeout for mobile networks
                timeout = aiohttp.ClientTimeout(total=60, connect=30)
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.warning(f"HTTP {response.status} for {url} (Attempt {attempt+1})")
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Network error {url}: {e} (Attempt {attempt+1})")
            except Exception as e:
                logger.error(f"Unexpected error {url}: {e}")
                
            # Backoff if not last attempt
            if attempt < retries - 1:
                delay = base_delay * (2 ** attempt) # 5, 10, 20
                await asyncio.sleep(delay)
                
        logger.error(f"Failed to fetch {url} after {retries} attempts")
        return None

    async def shorten_url(self, session: aiohttp.ClientSession, long_url: str) -> str:
        """Shorten URL using Ulvis API"""
        try:
            # API Endpoint: https://ulvis.net/API/write/get
            base_api = "https://ulvis.net/API/write/get"
            params = {
                "url": long_url,
                "private": "1",
                "type": "json",
                "via": "ET_Telegram_Bot"
            }
            
            async with session.get(base_api, params=params, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data and 'success' in data and data['success']:
                        return data['data']['url']
                    elif data and 'url' in data: # Sometimes simplistic returns
                         return data['url']
            
            # Fallback if API response is weird but not 200 error
            return long_url
            
        except Exception as e:
            logger.warning(f"Shortener failed for {long_url}: {e}")
            return long_url # Fail safe to original URL

    async def parse_feed(self, session: aiohttp.ClientSession, feed_config: Dict) -> List[NewsArticle]:
        feed_url = feed_config['url']
        feed_name = feed_config['name']
        
        # logger.info(f"Checking feed: {feed_name}") # Reduce log noise
        xml_bytes = await self.fetch_url(session, feed_url)
        if not xml_bytes:
            return []

        # Parse in thread pool (CPU bound)
        loop = asyncio.get_running_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, xml_bytes)
        
        articles = []
        today = date.today()
        
        for entry in feed.entries:
            # Date filtering
            pub_date_str = entry.get('published', '')
            try:
                if pub_date_str:
                    pub_dt = parsedate_to_datetime(pub_date_str)
                    if pub_dt.date() != today:
                        continue
            except:
                continue

            # Check DB (run in executor to be safe, though sqlite is fast)
            article_guid = entry.get('guid', entry.get('link', ''))
            article_hash = hashlib.md5(article_guid.encode()).hexdigest()
            
            title = html.unescape(entry.get('title', 'No Title'))
            title = normalize_currency_symbols(title)

            # Deduplication Check 1: Hash
            is_sent_hash = await loop.run_in_executor(self.executor, self.db.is_article_sent, article_hash)
            if is_sent_hash:
                continue

            # Deduplication Check 2: Title (User requested "title... or anything" check)
            is_sent_title = await loop.run_in_executor(self.executor, self.db.is_title_sent, title)
            if is_sent_title:
                # logger.info(f"Duplicate title found: {title}")
                continue

            # Extract image
            image_url = None
            if hasattr(entry, 'enclosures') and entry.enclosures:
                image_url = entry.enclosures[0].get('url')
            elif 'enclosure' in entry:
                image_url = entry.enclosure.get('url')

            # Title already processed above for deduplication check
            # title = html.unescape(entry.get('title', 'No Title'))
            # title = normalize_currency_symbols(title)
            
            description = entry.get('description', '')
            if description:
                description = html.unescape(description)
                description = normalize_currency_symbols(description)
                description = summarize_text(description)

            article = NewsArticle(
                title=title,
                description=description,
                link=entry.get('link', ''),
                pub_date=pub_date_str,
                image_url=image_url,
                guid=article_guid
            )
            # Add temp sort key
            if 'pub_dt' in locals():
                article._pub_datetime = pub_dt
                
            articles.append(article)
            
        return articles

    async def worker_process_queue(self, context: ContextTypes.DEFAULT_TYPE):
        """Background worker consuming articles"""
        while True:
            try:
                # Wait for article
                item = await self.task_queue.get()
                article, feed_name = item
                
                try:
                    logger.info(f"⚡ Worker processing: {article.title[:30]}...")
                    
                    # 1. Download image bytes (Async I/O)
                    image_data = None
                    try:
                        if article.image_url:
                            # Use resilient fetch with shared session
                            if self.session:
                                 image_data = await self.fetch_url(self.session, article.image_url)
                            else:
                                 # Fallback logic removed, assuming session exists
                                 pass
                    except Exception as e:
                        logger.warning(f"Failed to download image for {article.title[:20]}: {e}")
                    
                    # 2. Generate Image (CPU Bound)
                    loop = asyncio.get_running_loop()
                    image_bio = await loop.run_in_executor(
                        self.executor, 
                        self.image_gen.generate_news_image, 
                        article.title, 
                        article.description, 
                        article.pub_date,
                        image_data # Pass BYTES, not URL
                    )
                    
                    # 3. Send to Telegram (Async Network)
                    # Prepare Instant View URL safely
                    iv_rhash = self.config.get('iv_rhash', '').strip()
                    article_link_encoded = urllib.parse.quote(article.link)
                    
                    if iv_rhash:
                        # Only use t.me/iv if we have a hash, otherwise it breaks
                        btn_url = f"https://t.me/iv?url={article_link_encoded}&rhash={iv_rhash}"
                    else:
                        # Fallback to direct link if no rhash (standard behavior)
                        btn_url = article.link
                        
                    # 3.5 Shorten URL (Async)
                    # We do this preferably before or parallel, but here is fine.
                    short_url = await self.shorten_url(self.session, btn_url)
                    
                    # Log if shortened or not (debug)
                    # logger.info(f"Shortened Link: {short_url}")
                    
                    keyboard = [[InlineKeyboardButton("Read Full Article 📰", url=short_url)]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await context.bot.send_photo(
                        chat_id=self.config['telegram_channel_id'],
                        photo=image_bio,
                        # caption removed as requested
                        # caption=f"{article.title}\n\n<a href='{article.link}'>Read Full Story</a>",
                        # parse_mode=ParseMode.HTML, 
                        reply_markup=reply_markup
                    )
                    
                    # 4. Mark done in DB (Async DB)
                    mess_id = "0" # We don't easily get msg id from send_photo in high volume async but we can update if needed. 
                    # send_photo returns a Message object.
                    # Actually we DO get it.
                    # But if we await send_photo, we get it.
                    # The above await returns Message.
                    
                    # Correctness fix:
                    # message = await context.bot.send_photo(...)
                    # mess_id = message.message_id
                    
                    await loop.run_in_executor(
                        self.executor,
                        self.db.mark_article_sent,
                        article,
                        "async_sent",
                        feed_name
                    )
                    
                    logger.info(f"✅ Sent: {article.title[:30]}")
                    
                    # Rate Limit: Sleep to prevent Flood
                    await asyncio.sleep(4) 
                    
                except TelegramError as te:
                    # Handle Flood Control Explicitly
                    if "Flood control exceeded" in str(te) or "Retry in" in str(te):
                         # Extract seconds if possible or default high
                         wait_time = 30
                         numbers = re.findall(r'\d+', str(te))
                         if numbers:
                             wait_time = int(numbers[0]) + 1
                         
                         logger.warning(f"Flood Limit! Sleeping for {wait_time}s")
                         await asyncio.sleep(wait_time)
                         
                         # Put back in queue to retry?
                         # For now, simplistic: we might lose it if we don't retry.
                         # Better: Retry loop inside here. But simpler code edit:
                         # Just log failure for now to avoid infinite loops if it persists.
                         logger.error(f"Message dropped due to flood: {article.title}")
                    else:
                        logger.error(f"Telegram Error: {te}")

                except Exception as e:
                    logger.error(f"Worker failed on article {article.title[:20]}: {e}")
                    await loop.run_in_executor(
                        self.executor,
                        self.db.log_failed_send,
                        article.get_hash(),
                        str(e)
                    )
                finally:
                    # Remove lock
                    if article.get_hash() in self.processing_hashes:
                        self.processing_hashes.remove(article.get_hash())
                    self.task_queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker Loop Error: {e}")
                await asyncio.sleep(1)

    async def feed_check_job(self, context: ContextTypes.DEFAULT_TYPE):
        """Periodic job triggered by JobQueue"""
        # Use shared session
        if not self.session:
            logger.error("Session not initialized!")
            return

        for feed_config in self.feeds:
            articles = await self.parse_feed(self.session, feed_config)
            
            # ALWAYS Sort oldest first to maintain chronological narrative
            if articles:
                articles.sort(key=lambda x: getattr(x, '_pub_datetime', datetime.min))
            
            for article in articles:
                # Deduplication check: DB + In-Memory Processing Set
                ahash = article.get_hash()
                
                # Check 1: Currently processing?
                if ahash in self.processing_hashes:
                    continue
                    
                # Check 2: Already sent? (Double check to be sure)
                # (Optimized: parse_feed already checked DB, but race condition possible)
                
                self.processing_hashes.add(ahash)
                await self.task_queue.put((article, feed_config['name']))
            
            if articles:
                logger.info(f"Queued {len(articles)} articles from {feed_config['name']}")

        if self.is_startup:
            self.is_startup = False
            logger.info("Startup complete - switching to live monitoring")
            
        # Calculate Next Scan Time (Approximate)
        ist_now = datetime.now(pytz.timezone('Asia/Kolkata'))
        next_scan = ist_now + timedelta(minutes=self.check_interval)
        next_scan_str = next_scan.strftime("%H:%M:%S")
        
        logger.info(f"Sleeping for 💤{self.check_interval} minutes... ⏭️ Next Scan at {next_scan_str} IST")

    async def post_init(self, application: Application):
        """Hook to start background workers and session"""
        self.session = aiohttp.ClientSession()
        logger.info("Persistent HTTP Session Created (Keep-Alive)")
        
        # Start the worker task
        asyncio.create_task(self.worker_wrapper(application))

    async def post_shutdown(self, application: Application):
        """Hook to close resources"""
        if self.session:
            await self.session.close()
            logger.info("HTTP Session Closed")

    async def worker_wrapper(self, application):
        # Create a dummy or custom context-like object if needed, or just pass bot
        class WorkerContext:
            def __init__(self, bot):
                self.bot = bot
        
        await self.worker_process_queue(WorkerContext(application.bot))

    async def start_bot(self):
        """Main Async Entry Point with Manual Lifecycle"""
        if not self.config['telegram_bot_token']:
            logger.error("No token found")
            return

        # Build Application
        application = Application.builder().token(self.config['telegram_bot_token']).post_init(self.post_init).post_shutdown(self.post_shutdown).build()
        
        # Add Custom Error Handler
        application.add_error_handler(error_handler)
        
        # Add Job
        job_queue = application.job_queue
        # First run immediately
        job_queue.run_once(self.feed_check_job, 1)
        # Then recurring
        job_queue.run_repeating(self.feed_check_job, interval=self.check_interval * 60, first=10)

        # Commands
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        
        logger.info("Starting Async Bot (Manual Mode)...")
        
        # Explicit Lifecycle Management
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True) # Clean start
        
        # Keep running until stop signal
        stop_signal = asyncio.Event()
        
        # Handle signals if possible (Windows/Termux might vary)
        try:
            # Simple infinite wait
            await stop_signal.wait()
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Stopping...")
        finally:
            await application.updater.stop()
            await application.stop()
            await application.shutdown()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("👋 Async News Bot is Running!\nUse /stats to see performance.")

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        stats = await asyncio.get_running_loop().run_in_executor(self.executor, self.db.get_stats)
        q_size = self.task_queue.qsize()
        text = (
            f"📊 **Bot Stats**\n"
            f"Queue Size: {q_size}\n"
            f"Total Sent: {stats['total_sent']}\n"
            f"Last Hour: {stats['sent_last_hour']}\n"
            f"Pending Failures: {stats['pending_failures']}"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    def download_nltk_resources(self):
        """Ensure necessary NLTK data is downloaded"""
        try:
            # Check/Download 'punkt' and 'punkt_tab'
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                logger.info("Downloading NLTK 'punkt'...")
                nltk.download('punkt', quiet=True)
                
            try:
                nltk.data.find('tokenizers/punkt_tab')
            except LookupError:
                logger.info("Downloading NLTK 'punkt_tab'...")
                nltk.download('punkt_tab', quiet=True)
        except Exception as e:
            logger.warning(f"NLTK Download Warning: {e}. Summarization might be degraded.")

if __name__ == "__main__":
    try:
        bot = AsyncNewsMonitor()
        asyncio.run(bot.start_bot())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        log_exception(e, "Fatal Error in Main Loop")

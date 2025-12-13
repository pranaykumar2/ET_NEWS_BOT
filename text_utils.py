"""
Text Processing Utilities
Provides efficient summarization using Sumy with resource reuse.
"""

import re
import logging
import nltk
from typing import Optional
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.utils import get_stop_words
from sumy.nlp.stemmers import Stemmer

logger = logging.getLogger(__name__)

# Ensure NLTK data is available
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    logger.info("Downloading missing NLTK 'punkt' data...")
    nltk.download('punkt', quiet=True)

class TextSummarizer:
    """
    Singleton-like helper to handle summarization efficiently.
    Initializes heavy NLP resources once.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TextSummarizer, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance

    def initialize(self):
        """Initialize language resources."""
        try:
            self.language = "english"
            self.stemmer = Stemmer(self.language)
            self.summarizer = LsaSummarizer(self.stemmer)
            self.summarizer.stop_words = get_stop_words(self.language)
            self.tokenizer = Tokenizer(self.language)
            logger.info("TextSummarizer initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize TextSummarizer: {e}")
            self.summarizer = None

    def clean_text(self, text: str) -> str:
        """Remove HTML and extra whitespace."""
        text = re.sub('<[^<]+?>', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def summarize(self, text: str, max_chars: int = 350, sentences_count: int = 2) -> str:
        """
        Summarize text using LSA.
        Falls back to intelligent truncation if summarization fails or is not helpful.
        """
        text = self.clean_text(text)
        
        if not text:
            return ""

        if len(text) <= max_chars:
            return text

        summary_text = ""
        
        if self.summarizer:
            try:
                parser = PlaintextParser.from_string(text, self.tokenizer)
                summary = self.summarizer(parser.document, sentences_count)
                summary_text = ' '.join([str(s) for s in summary])
            except Exception as e:
                logger.warning(f"Summarization error: {e}")
        
        # Fallback if LSA failed or returned empty
        if not summary_text:
             summary_text = text

        # Final truncation check
        if len(summary_text) > max_chars:
            return self.smart_truncate(summary_text, max_chars)
        
        return summary_text

    def smart_truncate(self, text: str, max_chars: int) -> str:
        """Truncate text at the nearest sentence or word boundary."""
        if len(text) <= max_chars:
            return text
            
        excerpt = text[:max_chars]
        
        # Try to cut at last period
        last_dot = excerpt.rfind('.')
        if last_dot > 50: # Ensure we have at least some content
            return excerpt[:last_dot+1]
            
        # Fallback: Split by space
        return excerpt.rsplit(' ', 1)[0] + '...'

# Global instance for easy import
summarizer = TextSummarizer()

def normalize_currency_symbols(text: str) -> str:
    """Replace currency symbols with codes, respecting word boundaries for text codes."""
    # 1. Symbol Replacement (Safe to replace directly usually, but regex is cleaner)
    symbol_map = {
        '₹': 'INR ', '₨': 'INR ', '$': 'USD ', '€': 'EUR ', '£': 'GBP ',
        '¥': 'JPY ', '₩': 'KRW ', '₽': 'RUB '
    }
    for symbol, replacement in symbol_map.items():
        text = text.replace(symbol, replacement)
        
    # 2. Text Code Replacement (Must use word boundaries)
    # rs/Rs -> INR (matches "Rs 500", "rs. 500", but not "worst")
    text = re.sub(r'\b(rs|Rs|RS)\.?\s+', 'INR ', text)
    
    return re.sub(r'\s+', ' ', text)

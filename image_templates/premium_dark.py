"""
Modern news image generator with fresh, contemporary design.
Clean, bold, and visually striking aesthetic.
"""

import logging
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
from typing import Optional
import requests
from config import Config
import os
from pathlib import Path
import math
import re
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

logger = logging.getLogger(__name__)


class EnhancedNewsImageGenerator:
    """Generates modern news images with contemporary design."""

    def __init__(self):
        """Initialize with design parameters."""
        self.width = 1200
        self.min_height = 675  # Minimum height, will expand based on content

        # Modern color palette
        self.bg_primary = (15, 23, 42)  # Slate 900
        self.bg_secondary = (30, 41, 59)  # Slate 800
        self.accent_blue = (59, 130, 246)  # Blue 500
        self.accent_orange = (251, 146, 60)  # Orange 400
        self.text_primary = (248, 250, 252)  # Slate 50
        self.text_secondary = (148, 163, 184)  # Slate 400
        
        # Load config colors for compatibility
        self.tag_bg_color = Config.TAG_BG_COLOR
        self.tag_text_color = Config.TAG_TEXT_COLOR
        self.title_color = Config.TITLE_COLOR
        self.description_color = Config.DESCRIPTION_COLOR

        # Font configurations from Config
        self.font_title_family = getattr(Config, 'FONT_TITLE_FAMILY', 'Inter')
        self.font_description_family = getattr(Config, 'FONT_DESCRIPTION_FAMILY', 'Inter')
        self.font_tag_family = getattr(Config, 'FONT_TAG_FAMILY', 'Inter')
        
        self.font_title_style = getattr(Config, 'FONT_TITLE_STYLE', '700')
        self.font_description_style = getattr(Config, 'FONT_DESCRIPTION_STYLE', '400')
        self.font_tag_style = getattr(Config, 'FONT_TAG_STYLE', '600')
        
        # Font sizes
        self.font_tag_size = getattr(Config, 'FONT_TAG_SIZE', 16)
        self.font_title_size = getattr(Config, 'FONT_TITLE_SIZE', 52)
        self.font_description_size = getattr(Config, 'FONT_DESCRIPTION_SIZE', 20)
        
        self.try_load_fonts()

    def download_google_font(self, font_family, weight='400'):
        """Download Google Font from CDN."""
        if not font_family:
            return None

        cache_dir = Path(__file__).parent / 'fonts_cache'
        cache_dir.mkdir(exist_ok=True)

        font_filename = f"{font_family.replace(' ', '')}-{weight}.ttf"
        font_path = cache_dir / font_filename

        if font_path.exists():
            return str(font_path)

        try:
            font_name_encoded = font_family.replace(' ', '+')
            api_url = f"https://fonts.googleapis.com/css2?family={font_name_encoded}:wght@{weight}&display=swap"

            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()

            import re
            font_urls = re.findall(r'src:\s*url\(([^)]+)\)', response.text)

            if font_urls:
                font_url = font_urls[0].strip()
                font_response = requests.get(font_url, timeout=15)
                font_response.raise_for_status()

                with open(font_path, 'wb') as f:
                    f.write(font_response.content)

                logger.info(f"Downloaded Google Font: {font_family} ({weight})")
                return str(font_path)

        except Exception as e:
            logger.warning(f"Could not download font {font_family}: {e}")

        return None

    def load_system_font(self, size):
        """Load system font with fallback."""
        fonts_to_try = [
            'arial.ttf',
            'Arial.ttf',
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/System/Library/Fonts/Helvetica.ttc',
        ]
        
        for font_path in fonts_to_try:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        
        return ImageFont.load_default()

    def try_load_fonts(self):
        """Load modern fonts based on configuration."""
        try:
            # Load title font
            title_font_path = self.download_google_font(self.font_title_family, self.font_title_style)
            if title_font_path:
                self.font_title = ImageFont.truetype(title_font_path, self.font_title_size)
            else:
                self.font_title = self.load_system_font(self.font_title_size)
            
            # Load description font
            description_font_path = self.download_google_font(self.font_description_family, 
                                                             self.font_description_style)
            if description_font_path:
                self.font_body = ImageFont.truetype(description_font_path, self.font_description_size)
            else:
                self.font_body = self.load_system_font(self.font_description_size)
            
            # Load tag font
            tag_font_path = self.download_google_font(self.font_tag_family, self.font_tag_style)
            if tag_font_path:
                self.font_tag = ImageFont.truetype(tag_font_path, self.font_tag_size)
            else:
                self.font_tag = self.load_system_font(self.font_tag_size)
                
        except Exception as e:
            logger.warning(f"Error loading fonts: {e}")
            self.font_title = self.load_system_font(self.font_title_size)
            self.font_body = self.load_system_font(self.font_description_size)
            self.font_tag = self.load_system_font(self.font_tag_size)

    def create_modern_background(self, height: int) -> Image:
        """Create modern gradient background with geometric patterns."""
        img = Image.new('RGB', (self.width, height), self.bg_primary)
        draw = ImageDraw.Draw(img)
        
        # Diagonal gradient overlay
        overlay = Image.new('RGBA', (self.width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Create diagonal gradient bands
        for i in range(0, self.width + height, 3):
            alpha = int(30 * (1 - i / (self.width + height)))
            overlay_draw.line([(i, 0), (0, i)], fill=(255, 255, 255, alpha), width=2)
        
        overlay = overlay.filter(ImageFilter.GaussianBlur(50))
        img.paste(overlay, (0, 0), overlay)
        
        # Add colored accent circles
        accent_overlay = Image.new('RGBA', (self.width, height), (0, 0, 0, 0))
        accent_draw = ImageDraw.Draw(accent_overlay)
        
        # Blue accent
        accent_draw.ellipse([self.width - 300, -100, self.width + 100, 300], 
                           fill=self.accent_blue + (25,))
        # Orange accent
        accent_draw.ellipse([-150, height - 250, 250, height + 150], 
                           fill=self.accent_orange + (20,))
        
        accent_overlay = accent_overlay.filter(ImageFilter.GaussianBlur(80))
        img.paste(accent_overlay, (0, 0), accent_overlay)
        
        return img

    def draw_pill_shape(self, draw, xy, fill):
        """Draw pill/capsule shape."""
        x1, y1, x2, y2 = xy
        radius = (y2 - y1) // 2
        
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
        draw.ellipse([x1, y1, x1 + radius * 2, y2], fill=fill)
        draw.ellipse([x2 - radius * 2, y1, x2, y2], fill=fill)

    def wrap_text(self, text, font, max_width):
        """Wrap text to fit width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))
        return lines

    def smart_reduce_text(self, text: str, max_chars: int) -> str:
        """Intelligently reduce text using LSA summarization."""
        try:
            text = re.sub('<[^<]+?>', '', text)
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            if not text or len(text) <= max_chars:
                return text
            
            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            stemmer = Stemmer("english")
            summarizer = LsaSummarizer(stemmer)
            summarizer.stop_words = get_stop_words("english")
            
            for sentence_count in [2, 1, 3]:
                summary_sentences = summarizer(parser.document, sentence_count)
                summary_text = ' '.join([str(sentence) for sentence in summary_sentences])
                
                if len(summary_text) <= max_chars:
                    return summary_text
                
                if sentence_count == 1 and len(summary_text) > max_chars:
                    truncated = summary_text[:max_chars].rsplit('.', 1)[0]
                    if len(truncated) > 50:
                        return truncated
            
            sentences = text.split('. ')
            result = sentences[0]
            if len(result) > max_chars:
                result = result[:max_chars].rsplit(' ', 1)[0]
            return result
            
        except Exception as e:
            logger.warning(f"Smart reduce failed: {e}")
            if len(text) > max_chars:
                return text[:max_chars].rsplit(' ', 1)[0]
            return text

    def summarize_to_fit(self, text: str, font, max_width: int, max_lines: int, line_height: int) -> str:
        """Intelligently reduce text to fit within line constraints."""
        lines = self.wrap_text(text, font, max_width)
        
        if len(lines) <= max_lines:
            return text
        
        avg_chars_per_line = len(text) // max(len(lines), 1)
        target_chars = avg_chars_per_line * max_lines
        
        reduced_text = self.smart_reduce_text(text, target_chars)
        
        lines = self.wrap_text(reduced_text, font, max_width)
        while len(lines) > max_lines and len(reduced_text) > 50:
            target_chars = int(target_chars * 0.85)
            reduced_text = self.smart_reduce_text(text, target_chars)
            lines = self.wrap_text(reduced_text, font, max_width)
        
        return reduced_text

    def download_image(self, url):
        """Download and prepare image."""
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content))
            return img.convert('RGB')
        except:
            return None

    def generate_news_image(self, title, description="", timestamp="", image_url=""):
        """Generate modern news image with fresh design and dynamic height.

        Args:
            title: News headline
            description: News description
            timestamp: Publication time
            image_url: Optional news image URL

        Returns:
            BytesIO containing PNG image
        """
        # Calculate required height based on ALL content
        padding = 60
        content_start_y = 80 + 40  # After live indicator
        
        # Determine text area width
        if image_url:
            text_width = int(self.width * 0.55)
            text_area_width = text_width - (padding * 2)
        else:
            text_area_width = self.width - (padding * 2)
        
        # Calculate title height - wrap ALL lines
        title_lines = self.wrap_text(title, self.font_title, text_area_width if image_url else text_area_width)
        title_height = len(title_lines) * 65
        
        # Calculate description height - wrap ALL lines
        desc_height = 0
        if description:
            desc_lines = self.wrap_text(description, self.font_body, text_area_width if image_url else int(text_area_width * 0.8))
            desc_height = len(desc_lines) * 32 + 25
        
        # Calculate total required height
        footer_height = 120
        content_height = content_start_y + 20 + title_height + desc_height + footer_height
        
        # Use calculated height to fit all content
        actual_height = max(self.min_height, content_height)
        
        # Create background with dynamic height
        base = self.create_modern_background(actual_height)
        draw = ImageDraw.Draw(base)
        
        # Layout parameters
        padding = 60
        content_start_y = 80
        
        # Live indicator badge
        badge_x = padding
        badge_y = content_start_y
        badge_text = "LIVE"
        
        # Draw pulsing live indicator
        pulse_overlay = Image.new('RGBA', (self.width, actual_height), (0, 0, 0, 0))
        pulse_draw = ImageDraw.Draw(pulse_overlay)
        
        # Outer pulse glow
        pulse_draw.ellipse([badge_x - 5, badge_y - 5, badge_x + 15, badge_y + 15], 
                          fill=(239, 68, 68, 40))
        pulse_overlay = pulse_overlay.filter(ImageFilter.GaussianBlur(8))
        base.paste(pulse_overlay, (0, 0), pulse_overlay)
        
        # Live dot
        draw.ellipse([badge_x, badge_y, badge_x + 10, badge_y + 10], 
                    fill=(239, 68, 68))
        
        # Live text
        draw.text((badge_x + 20, badge_y - 3), badge_text, 
                 fill=(239, 68, 68), font=self.font_tag)
        
        content_start_y += 40
        
        # Main content area
        if image_url:
            # Split layout: text on left, image on right
            text_width = int(self.width * 0.55)
            text_area_width = text_width - (padding * 2)
            
            # Title - show ALL lines
            title_y = content_start_y + 20
            title_lines = self.wrap_text(title, self.font_title, text_area_width)
            
            for i, line in enumerate(title_lines):  # Show ALL title lines
                # Text with subtle shadow
                draw.text((padding + 2, title_y + 2), line, 
                         fill=(0, 0, 0, 100), font=self.font_title)
                draw.text((padding, title_y), line, 
                         fill=self.text_primary, font=self.font_title)
                title_y += 65
            
            # Description - show ALL lines
            if description:
                desc_y = title_y + 25
                desc_lines = self.wrap_text(description, self.font_body, text_area_width)
                
                for i, line in enumerate(desc_lines):  # Show ALL description lines
                    draw.text((padding, desc_y), line, 
                             fill=self.text_secondary, font=self.font_body)
                    desc_y += 32
            
            # Accent line
            line_y = actual_height - 100
            draw.rectangle([padding, line_y, padding + 80, line_y + 4], 
                          fill=self.accent_blue)
            
            # Timestamp or source
            if timestamp:
                draw.text((padding, line_y + 20), timestamp, 
                         fill=self.text_secondary, font=self.font_tag)
            
            # Image on right side
            news_img = self.download_image(image_url)
            if news_img:
                img_x = text_width + 30
                img_y = content_start_y
                img_max_width = self.width - img_x - padding
                img_max_height = actual_height - img_y - padding
                
                # Resize image
                aspect = news_img.width / news_img.height
                if aspect > (img_max_width / img_max_height):
                    new_width = img_max_width
                    new_height = int(new_width / aspect)
                else:
                    new_height = img_max_height
                    new_width = int(new_height * aspect)
                
                news_img = news_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Center image vertically
                img_y = content_start_y + (img_max_height - new_height) // 2
                
                # Create rounded mask with border
                border_size = 3
                
                # Draw border shadow
                shadow_overlay = Image.new('RGBA', (self.width, actual_height), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow_overlay)
                shadow_draw.rounded_rectangle(
                    [(img_x - border_size, img_y - border_size), 
                     (img_x + new_width + border_size, img_y + new_height + border_size)],
                    radius=20,
                    fill=(0, 0, 0, 60)
                )
                shadow_overlay = shadow_overlay.filter(ImageFilter.GaussianBlur(15))
                base.paste(shadow_overlay, (0, 0), shadow_overlay)
                
                # Draw border
                border_overlay = Image.new('RGBA', (self.width, actual_height), (0, 0, 0, 0))
                border_draw = ImageDraw.Draw(border_overlay)
                border_draw.rounded_rectangle(
                    [(img_x - border_size, img_y - border_size), 
                     (img_x + new_width + border_size, img_y + new_height + border_size)],
                    radius=20,
                    fill=self.accent_blue + (255,)
                )
                base.paste(border_overlay, (0, 0), border_overlay)
                
                # Paste image with rounded corners
                mask = Image.new('L', news_img.size, 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle(
                    [(0, 0), news_img.size],
                    radius=17,
                    fill=255
                )
                base.paste(news_img, (img_x, img_y), mask)
        
        else:
            # Full width text layout
            text_area_width = self.width - (padding * 2)
            
            # Title centered - show ALL lines
            title_y = content_start_y + 60
            title_lines = self.wrap_text(title, self.font_title, text_area_width)
            
            for line in title_lines:  # Show ALL title lines
                bbox = self.font_title.getbbox(line)
                text_width = bbox[2] - bbox[0]
                x_centered = (self.width - text_width) // 2
                
                # Shadow
                draw.text((x_centered + 2, title_y + 2), line, 
                         fill=(0, 0, 0, 100), font=self.font_title)
                # Text
                draw.text((x_centered, title_y), line, 
                         fill=self.text_primary, font=self.font_title)
                title_y += 65
            
            # Description centered - show ALL lines
            if description:
                desc_y = title_y + 40
                desc_lines = self.wrap_text(description, self.font_body, 
                                          int(text_area_width * 0.8))
                
                for line in desc_lines:  # Show ALL description lines
                    bbox = self.font_body.getbbox(line)
                    text_width = bbox[2] - bbox[0]
                    x_centered = (self.width - text_width) // 2
                    
                    draw.text((x_centered, desc_y), line, 
                             fill=self.text_secondary, font=self.font_body)
                    desc_y += 32
            
            # Centered accent line
            line_y = actual_height - 120
            line_width = 100
            draw.rectangle([(self.width - line_width) // 2, line_y, 
                          (self.width + line_width) // 2, line_y + 4], 
                          fill=self.accent_blue)
        
        # Save to BytesIO
        output = BytesIO()
        base.save(output, format='PNG', quality=95)
        output.seek(0)
        return output
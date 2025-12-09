"""
Premium light theme news image generator with ultimate UI/UX experience.
Clean, bright, and sophisticated aesthetic with modern design principles.
Configurable features for branding and visual style.
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


class PremiumLightNewsImageGenerator:
    """Generates premium light theme news images with exceptional UI/UX."""

    def __init__(self, 
                 show_brand=False, 
                 show_mesh_grid_background=True,
                 brand_name="Balaji Equities"):
        """
        Initialize with modern light theme design parameters.
        
        Args:
            show_brand: Show brand name in the image
            show_mesh_grid_background: Show mesh gradient grid background
            brand_name: Brand name to display (for header - not used currently)
        """
        self.width = 1200
        self.min_height = 675  # Minimum height, will expand based on content
        
        # Configuration flags
        self.show_brand = show_brand
        self.show_mesh_grid_background = show_mesh_grid_background
        self.brand_name = brand_name

        # Premium light color palette
        self.bg_primary = (255, 255, 255)  # Pure white
        self.bg_secondary = (249, 250, 251)  # Gray 50
        self.bg_accent = (243, 244, 246)  # Gray 100
        
        # Accent colors - vibrant but refined
        self.accent_blue = (37, 99, 235)  # Blue 600
        self.accent_purple = (147, 51, 234)  # Purple 600
        self.accent_emerald = (5, 150, 105)  # Emerald 600
        self.accent_orange = (234, 88, 12)  # Orange 600
        
        # Text colors
        self.text_primary = (17, 24, 39)  # Gray 900
        self.text_secondary = (75, 85, 99)  # Gray 600
        self.text_tertiary = (156, 163, 175)  # Gray 400
        
        # Live indicator
        self.live_red = (239, 68, 68)  # Red 500
        
        # Load config colors for compatibility
        self.tag_bg_color = Config.TAG_BG_COLOR
        self.tag_text_color = Config.TAG_TEXT_COLOR
        self.title_color = Config.TITLE_COLOR
        self.description_color = Config.DESCRIPTION_COLOR

        # Font configurations from Config
        self.font_title_family = getattr(Config, 'FONT_TITLE_FAMILY', 'Inter')
        self.font_description_family = getattr(Config, 'FONT_DESCRIPTION_FAMILY', 'Inter')
        self.font_tag_family = getattr(Config, 'FONT_TAG_FAMILY', 'Inter')
        self.font_brand_family = getattr(Config, 'FONT_BRAND_FAMILY', 'Inter')  # For copyright
        
        self.font_title_style = getattr(Config, 'FONT_TITLE_STYLE', '800')
        self.font_description_style = getattr(Config, 'FONT_DESCRIPTION_STYLE', '400')
        self.font_tag_style = getattr(Config, 'FONT_TAG_STYLE', '600')
        self.font_brand_style = getattr(Config, 'FONT_BRAND_STYLE', '400')  # For copyright
        
        # Font sizes - optimized for readability
        self.font_tag_size = getattr(Config, 'FONT_TAG_SIZE', 15)
        self.font_title_size = getattr(Config, 'FONT_TITLE_SIZE', 54)
        self.font_description_size = getattr(Config, 'FONT_DESCRIPTION_SIZE', 19)
        self.font_brand_size = getattr(Config, 'FONT_BRAND_SIZE', 13)  # For copyright text
        
        # Line heights for better text spacing
        self.title_line_height = getattr(Config, 'TITLE_LINE_HEIGHT', 52)
        self.description_line_height = getattr(Config, 'DESCRIPTION_LINE_HEIGHT', 38)
        
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
        """Load premium fonts for light theme based on configuration."""
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
            
            # Load brand font (for copyright text)
            brand_font_path = self.download_google_font(self.font_brand_family, 
                                                       self.font_brand_style)
            if brand_font_path:
                self.font_brand = ImageFont.truetype(brand_font_path, self.font_brand_size)
            else:
                self.font_brand = self.load_system_font(self.font_brand_size)
            
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
            self.font_brand = self.load_system_font(self.font_brand_size)

    def create_mesh_grid_background(self, height: int) -> Image:
        """Create sophisticated mesh gradient grid background with heavy blur for focus."""
        img = Image.new('RGB', (self.width, height), self.bg_primary)
        
        # Create mesh grid overlay
        mesh_overlay = Image.new('RGBA', (self.width, height), (0, 0, 0, 0))
        mesh_draw = ImageDraw.Draw(mesh_overlay)
        
        # Grid parameters
        grid_spacing = 80
        line_width = 2
        
        # Draw vertical grid lines with gradient
        for x in range(0, self.width, grid_spacing):
            # Vary opacity based on position
            opacity = int(15 * (1 - abs(x - self.width // 2) / (self.width // 2)))
            mesh_draw.line([(x, 0), (x, height)], 
                          fill=self.text_tertiary + (opacity,), width=line_width)
        
        # Draw horizontal grid lines with gradient
        for y in range(0, height, grid_spacing):
            opacity = int(15 * (1 - abs(y - height // 2) / (height // 2)))
            mesh_draw.line([(0, y), (self.width, y)], 
                          fill=self.text_tertiary + (opacity,), width=line_width)
        
        # Heavy blur to make it very subtle and non-distracting
        mesh_overlay = mesh_overlay.filter(ImageFilter.GaussianBlur(40))
        img.paste(mesh_overlay, (0, 0), mesh_overlay)
        
        # Add gradient color accents at intersection points
        accent_overlay = Image.new('RGBA', (self.width, height), (0, 0, 0, 0))
        accent_draw = ImageDraw.Draw(accent_overlay)
        
        # Strategic color placement for visual interest
        colors = [
            (self.accent_blue, self.width - 400, -150, self.width + 150, 400),
            (self.accent_purple, -200, height - 300, 300, height + 200),
            (self.accent_emerald, self.width // 2 - 200, height // 2 - 200, 
             self.width // 2 + 200, height // 2 + 200),
            (self.accent_orange, self.width - 200, height - 200, 
             self.width + 100, height + 100),
        ]
        
        for color, x1, y1, x2, y2 in colors:
            # Very low opacity for subtlety
            accent_draw.ellipse([x1, y1, x2, y2], fill=color + (8,))
        
        # Extra heavy blur for vanishing effect
        accent_overlay = accent_overlay.filter(ImageFilter.GaussianBlur(120))
        img.paste(accent_overlay, (0, 0), accent_overlay)
        
        # Add noise texture for depth (very subtle)
        import random
        random.seed(42)
        for _ in range(300):
            x = random.randint(0, self.width)
            y = random.randint(0, height)
            accent_draw.ellipse([x, y, x + 1, y + 1], fill=(0, 0, 0, 2))
        
        return img

    def create_simple_light_background(self, height: int) -> Image:
        """Create clean minimal background without mesh grid."""
        img = Image.new('RGB', (self.width, height), self.bg_primary)
        
        # Very subtle gradient overlay
        overlay = Image.new('RGBA', (self.width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Soft diagonal pattern
        for i in range(0, self.width + height, 6):
            alpha = int(5 * (i / (self.width + height)))
            overlay_draw.line([(i, 0), (0, i)], fill=(0, 0, 0, alpha), width=1)
        
        overlay = overlay.filter(ImageFilter.GaussianBlur(80))
        img.paste(overlay, (0, 0), overlay)
        
        # Minimal color accents
        accent_overlay = Image.new('RGBA', (self.width, height), (0, 0, 0, 0))
        accent_draw = ImageDraw.Draw(accent_overlay)
        
        # Single subtle accent
        accent_draw.ellipse([self.width - 400, -150, self.width + 150, 400], 
                           fill=self.accent_blue + (10,))
        
        accent_overlay = accent_overlay.filter(ImageFilter.GaussianBlur(100))
        img.paste(accent_overlay, (0, 0), accent_overlay)
        
        return img

    def draw_rounded_rectangle(self, draw, xy, radius, fill):
        """Draw rounded rectangle."""
        x1, y1, x2, y2 = xy
        draw.rounded_rectangle(xy, radius=radius, fill=fill)

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
        """Intelligently reduce text using LSA summarization.
        
        Args:
            text: Original text to reduce
            max_chars: Maximum characters allowed
            
        Returns:
            Intelligently reduced text that maintains meaning
        """
        try:
            # Clean up text
            text = re.sub('<[^<]+?>', '', text)
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()
            
            # If already short enough, return as is
            if not text or len(text) <= max_chars:
                return text
            
            # Try intelligent summarization with LSA
            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            stemmer = Stemmer("english")
            summarizer = LsaSummarizer(stemmer)
            summarizer.stop_words = get_stop_words("english")
            
            # Try different sentence counts
            for sentence_count in [2, 1, 3]:
                summary_sentences = summarizer(parser.document, sentence_count)
                summary_text = ' '.join([str(sentence) for sentence in summary_sentences])
                
                if len(summary_text) <= max_chars:
                    return summary_text
                
                # If 1 sentence still too long, truncate intelligently
                if sentence_count == 1 and len(summary_text) > max_chars:
                    truncated = summary_text[:max_chars].rsplit('.', 1)[0]
                    if len(truncated) > 50:
                        return truncated + '...'
            
            # Last resort: intelligent truncation at word boundary
            sentences = text.split('. ')
            result = sentences[0]
            if len(result) > max_chars:
                result = result[:max_chars].rsplit(' ', 1)[0] + '...'
            return result
            
        except Exception as e:
            logger.warning(f"Smart reduce failed: {e}, using simple truncation")
            # Fallback to simple truncation at word boundary
            if len(text) > max_chars:
                return text[:max_chars].rsplit(' ', 1)[0] + '...'
            return text

    def summarize_to_fit(self, text: str, font, max_width: int, max_lines: int, line_height: int) -> str:
        """Intelligently reduce text to fit within line constraints.
        
        Args:
            text: Original text
            font: Font to use for measurement
            max_width: Maximum width per line
            max_lines: Maximum number of lines allowed
            line_height: Height of each line
            
        Returns:
            Text reduced to fit within constraints while maintaining meaning
        """
        # First wrap to see how many lines we'd need
        lines = self.wrap_text(text, font, max_width)
        
        if len(lines) <= max_lines:
            return text
        
        # Calculate character budget based on typical chars per line
        avg_chars_per_line = len(text) // max(len(lines), 1)
        target_chars = avg_chars_per_line * max_lines
        
        # Reduce text intelligently
        reduced_text = self.smart_reduce_text(text, target_chars)
        
        # Verify it fits, if not reduce further
        lines = self.wrap_text(reduced_text, font, max_width)
        while len(lines) > max_lines and len(reduced_text) > 50:
            target_chars = int(target_chars * 0.85)  # Reduce by 15%
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
        """
        Generate premium light theme news image with ultimate UI/UX and dynamic height.
        Shows ALL text without truncation by expanding canvas dynamically.

        Args:
            title: News headline
            description: News description
            timestamp: Publication time (not displayed)
            image_url: Optional news image URL

        Returns:
            BytesIO containing PNG image
        """
        # Calculate required height based on ALL content (no limits)
        padding = 65
        content_start_y = 70
        
        # Determine text area width based on layout
        if image_url:
            text_width = int(self.width * 0.52)
            text_area_width = text_width - (padding * 2)
        else:
            text_area_width = self.width - (padding * 2)
        
        # Calculate title height - wrap ALL lines, no limit
        title_lines = self.wrap_text(title, self.font_title, text_area_width if image_url else int(text_area_width * 0.85))
        title_height = len(title_lines) * self.title_line_height
        
        # Calculate description height - wrap ALL lines, no limit
        desc_height = 0
        if description:
            desc_lines = self.wrap_text(description, self.font_body, text_area_width if image_url else int(text_area_width * 0.7))
            desc_height = len(desc_lines) * self.description_line_height + 30
        
        # Calculate total required height to fit ALL content
        tag_height = 40
        footer_height = 100
        content_height = content_start_y + tag_height + 35 + title_height + desc_height + footer_height
        
        # Always use calculated height to fit all content (no min constraint if content is larger)
        actual_height = max(self.min_height, content_height)
        
        # Create background with dynamic height
        if self.show_mesh_grid_background:
            base = self.create_mesh_grid_background(actual_height)
        else:
            base = self.create_simple_light_background(actual_height)
        
        draw = ImageDraw.Draw(base)
        
        # Layout parameters
        padding = 65
        content_start_y = 70
        
        # Brand header (optional) - shows brand_name at top
        if self.show_brand:
            brand_height = 50
            brand_overlay = Image.new('RGBA', (self.width, actual_height), (0, 0, 0, 0))
            brand_draw = ImageDraw.Draw(brand_overlay)
            
            # Subtle gradient header
            for i in range(brand_height):
                alpha = int(20 * (1 - i / brand_height))
                brand_draw.rectangle([0, i, self.width, i + 1], 
                                    fill=self.accent_blue + (alpha,))
            
            base.paste(brand_overlay, (0, 0), brand_overlay)
            
            # Brand name at top (different from copyright)
            brand_header_text = self.brand_name.upper()
            brand_bbox = self.font_tag.getbbox(brand_header_text)
            brand_width = brand_bbox[2] - brand_bbox[0]
            brand_x = (self.width - brand_width) // 2
            brand_y = 16
            
            # Brand text with subtle shadow
            draw.text((brand_x + 1, brand_y + 1), brand_header_text, 
                     fill=self.text_tertiary, font=self.font_tag)
            draw.text((brand_x, brand_y), brand_header_text, 
                     fill=self.accent_blue, font=self.font_tag)
            
            content_start_y = brand_height + 30
        
        # Main content area
        if image_url:
            # Split layout: text on left, image on right
            text_width = int(self.width * 0.52)
            text_area_width = text_width - (padding * 2)
            
            # Category tag
            category_tag = "LIVE MARKET UPDATES"  
            tag_x = padding
            tag_y = content_start_y
            
            tag_bbox = self.font_tag.getbbox(category_tag)
            tag_width = tag_bbox[2] - tag_bbox[0] + 24
            tag_height = 45
            
            # Tag background with shadow
            shadow_overlay = Image.new('RGBA', (self.width, actual_height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_overlay)
            shadow_draw.rounded_rectangle(
                [(tag_x, tag_y), (tag_x + tag_width, tag_y + tag_height)],
                radius=16,
                fill=(0, 0, 0, 20)
            )
            shadow_overlay = shadow_overlay.filter(ImageFilter.GaussianBlur(8))
            base.paste(shadow_overlay, (0, 0), shadow_overlay)
            
            # Tag background
            draw.rounded_rectangle(
                [(tag_x, tag_y), (tag_x + tag_width, tag_y + tag_height)],
                radius=16,
                fill=self.accent_blue
            )
            
            # Tag text
            draw.text((tag_x + 12, tag_y + 8), category_tag, 
                     fill=(255, 255, 255), font=self.font_tag)
            
            # Title with premium spacing - show ALL lines
            title_y = tag_y + tag_height + 35
            title_lines = self.wrap_text(title, self.font_title, text_area_width)
            
            for i, line in enumerate(title_lines):  # Show ALL title lines, no limit
                # Subtle text shadow for depth
                shadow_color = self.text_tertiary
                draw.text((padding + 1, title_y + 1), line, 
                         fill=shadow_color, font=self.font_title)
                # Main text
                draw.text((padding, title_y), line, 
                         fill=self.text_primary, font=self.font_title)
                title_y += self.title_line_height
            
            # Description with optimal line height - show ALL lines
            if description:
                desc_y = title_y + 30
                desc_lines = self.wrap_text(description, self.font_body, text_area_width)
                
                for i, line in enumerate(desc_lines):  # Show ALL description lines, no limit
                    draw.text((padding, desc_y), line, 
                             fill=self.text_secondary, font=self.font_body)
                    desc_y += self.description_line_height
            
            # Decorative accent line
            line_y = actual_height - 75
            gradient_line = Image.new('RGBA', (self.width, actual_height), (0, 0, 0, 0))
            gradient_draw = ImageDraw.Draw(gradient_line)
            
            # Gradient line effect
            line_width = 120
            for i in range(line_width):
                alpha = int(255 * (1 - i / line_width))
                gradient_draw.rectangle([padding + i, line_y, padding + i + 1, line_y + 5], 
                                       fill=self.accent_blue + (alpha,))
            
            base.paste(gradient_line, (0, 0), gradient_line)
            
            # Copyright text (using brand font configuration)
            copyright_text = "© 2025 Balaji Equities Ltd."
            draw.text((padding, line_y + 16), copyright_text, 
                     fill=self.text_tertiary, font=self.font_brand)
            
            # Premium image display on right
            news_img = self.download_image(image_url)
            if news_img:
                img_x = text_width + 40
                img_y = content_start_y
                img_max_width = self.width - img_x - padding
                img_max_height = actual_height - img_y - padding
                
                # Resize image maintaining aspect ratio
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
                
                # Premium shadow effect
                shadow_size = 30
                shadow_overlay = Image.new('RGBA', (self.width, actual_height), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow_overlay)
                shadow_draw.rounded_rectangle(
                    [(img_x - shadow_size // 2, img_y - shadow_size // 2), 
                     (img_x + new_width + shadow_size // 2, img_y + new_height + shadow_size // 2)],
                    radius=24,
                    fill=(0, 0, 0, 40)
                )
                shadow_overlay = shadow_overlay.filter(ImageFilter.GaussianBlur(20))
                base.paste(shadow_overlay, (0, 0), shadow_overlay)
                
                # White border frame
                border_size = 8
                border_overlay = Image.new('RGBA', (self.width, actual_height), (0, 0, 0, 0))
                border_draw = ImageDraw.Draw(border_overlay)
                border_draw.rounded_rectangle(
                    [(img_x - border_size, img_y - border_size), 
                     (img_x + new_width + border_size, img_y + new_height + border_size)],
                    radius=20,
                    fill=(255, 255, 255, 255)
                )
                base.paste(border_overlay, (0, 0), border_overlay)
                
                # Accent gradient border
                accent_border_size = 3
                accent_border = Image.new('RGBA', (self.width, actual_height), (0, 0, 0, 0))
                accent_draw = ImageDraw.Draw(accent_border)
                accent_draw.rounded_rectangle(
                    [(img_x - border_size - accent_border_size, img_y - border_size - accent_border_size), 
                     (img_x + new_width + border_size + accent_border_size, 
                      img_y + new_height + border_size + accent_border_size)],
                    radius=22,
                    outline=self.accent_blue + (150,),
                    width=accent_border_size
                )
                base.paste(accent_border, (0, 0), accent_border)
                
                # Paste image with rounded corners
                mask = Image.new('L', news_img.size, 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle(
                    [(0, 0), news_img.size],
                    radius=15,
                    fill=255
                )
                base.paste(news_img, (img_x, img_y), mask)
        
        else:
            # Full width centered layout
            text_area_width = self.width - (padding * 2)
            
            # Category tag centered
            category_tag = "BREAKING NEWS"
            tag_bbox = self.font_tag.getbbox(category_tag)
            tag_width = tag_bbox[2] - tag_bbox[0] + 24
            tag_height = 32
            tag_x = (self.width - tag_width) // 2
            tag_y = content_start_y + 20
            
            # Tag with shadow
            shadow_overlay = Image.new('RGBA', (self.width, actual_height), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_overlay)
            shadow_draw.rounded_rectangle(
                [(tag_x, tag_y), (tag_x + tag_width, tag_y + tag_height)],
                radius=16,
                fill=(0, 0, 0, 20)
            )
            shadow_overlay = shadow_overlay.filter(ImageFilter.GaussianBlur(8))
            base.paste(shadow_overlay, (0, 0), shadow_overlay)
            
            draw.rounded_rectangle(
                [(tag_x, tag_y), (tag_x + tag_width, tag_y + tag_height)],
                radius=16,
                fill=self.accent_blue
            )
            draw.text((tag_x + 12, tag_y + 8), category_tag, 
                     fill=(255, 255, 255), font=self.font_tag)
            
            # Title centered - show ALL lines
            title_y = tag_y + tag_height + 45
            title_lines = self.wrap_text(title, self.font_title, int(text_area_width * 0.85))
            
            for line in title_lines:  # Show ALL title lines, no limit
                bbox = self.font_title.getbbox(line)
                text_width = bbox[2] - bbox[0]
                x_centered = (self.width - text_width) // 2
                
                # Shadow
                draw.text((x_centered + 1, title_y + 1), line, 
                         fill=self.text_tertiary, font=self.font_title)
                # Text
                draw.text((x_centered, title_y), line, 
                         fill=self.text_primary, font=self.font_title)
                title_y += self.title_line_height
            
            # Description centered - show ALL lines
            if description:
                desc_y = title_y + 35
                desc_lines = self.wrap_text(description, self.font_body, int(text_area_width * 0.7))
                
                for line in desc_lines:  # Show ALL description lines, no limit
                    bbox = self.font_body.getbbox(line)
                    text_width = bbox[2] - bbox[0]
                    x_centered = (self.width - text_width) // 2
                    
                    draw.text((x_centered, desc_y), line, 
                             fill=self.text_secondary, font=self.font_body)
                    desc_y += self.description_line_height
            
            # Centered decorative element
            line_y = actual_height - 85
            line_width = 140
            line_x = (self.width - line_width) // 2
            
            # Gradient line
            gradient_line = Image.new('RGBA', (self.width, actual_height), (0, 0, 0, 0))
            gradient_draw = ImageDraw.Draw(gradient_line)
            
            for i in range(line_width):
                progress = abs(i - line_width // 2) / (line_width // 2)
                alpha = int(255 * (1 - progress))
                gradient_draw.rectangle([line_x + i, line_y, line_x + i + 1, line_y + 5], 
                                       fill=self.accent_blue + (alpha,))
            
            base.paste(gradient_line, (0, 0), gradient_line)
            
            # Copyright centered (using brand font configuration)
            copyright_text = "© 2025 Balaji Equities Ltd."
            copyright_bbox = self.font_brand.getbbox(copyright_text)
            copyright_width = copyright_bbox[2] - copyright_bbox[0]
            copyright_x = (self.width - copyright_width) // 2
            
            draw.text((copyright_x, line_y + 16), copyright_text, 
                     fill=self.text_tertiary, font=self.font_brand)
        
        # Save to BytesIO
        output = BytesIO()
        base.save(output, format='PNG', quality=98, optimize=True)
        output.seek(0)
        return output
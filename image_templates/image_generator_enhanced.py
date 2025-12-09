"""
Enhanced modern news image generator with improved styling.
All colors and sizes configurable via .env file.
"""

import logging
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
from typing import Optional
import requests
from config import Config
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class EnhancedNewsImageGenerator:
    """Generates enhanced modern news images with improved style."""

    def __init__(self):
        """Initialize with enhanced design parameters from Config."""
        self.width = 1400
        self.min_height = 900  # Minimum height, will expand based on content

        # Load colors from Config (.env)
        self.bg_black = Config.BG_BLACK
        self.bg_grey = Config.BG_GREY
        self.card_bg = Config.CARD_BG

        self.tag_bg_color = Config.TAG_BG_COLOR
        self.tag_text_color = Config.TAG_TEXT_COLOR

        self.title_color = Config.TITLE_COLOR
        self.description_color = Config.DESCRIPTION_COLOR
        self.brand_color = Config.BRAND_COLOR

        self.sky_blue = Config.SKY_BLUE
        self.light_green = Config.LIGHT_GREEN

        # Load font sizes from Config (.env)
        self.font_tag_size = Config.FONT_TAG_SIZE
        self.font_title_size = Config.FONT_TITLE_SIZE
        self.font_description_size = Config.FONT_DESCRIPTION_SIZE
        self.font_brand_size = Config.FONT_BRAND_SIZE

        # Load font styles from Config (.env)
        self.font_tag_style = Config.FONT_TAG_STYLE
        self.font_title_style = Config.FONT_TITLE_STYLE
        self.font_description_style = Config.FONT_DESCRIPTION_STYLE
        self.font_brand_style = Config.FONT_BRAND_STYLE

        # Load font families from Config (.env)
        self.font_tag_family = Config.FONT_TAG_FAMILY
        self.font_title_family = Config.FONT_TITLE_FAMILY
        self.font_description_family = Config.FONT_DESCRIPTION_FAMILY
        self.font_brand_family = Config.FONT_BRAND_FAMILY

        self.try_load_fonts()

    def download_google_font(self, font_family, style):
        """Download Google Font from CDN and cache it locally."""
        if not font_family:
            return None

        # Create fonts cache directory
        cache_dir = Path(__file__).parent / 'fonts_cache'
        cache_dir.mkdir(exist_ok=True)

        # Map style to Google Fonts parameters
        if style == 'bold':
            weight = '700'
            italic = ''
        elif style == 'italic':
            weight = '400'
            italic = 'ital,'
        else:  # normal
            weight = '400'
            italic = ''

        # Check if font is already cached
        font_filename = f"{font_family.replace(' ', '')}-{style}.ttf"
        font_path = cache_dir / font_filename

        if font_path.exists():
            logger.info(f"Using cached font: {font_family} ({style})")
            return str(font_path)

        # Download from Google Fonts CDN
        try:
            # Request font CSS with proper User-Agent to get TTF files
            font_name_encoded = font_family.replace(' ', '+')

            # For italic fonts, use ital,wght format
            if italic:
                api_url = f"https://fonts.googleapis.com/css2?family={font_name_encoded}:ital,wght@1,{weight}&display=swap"
            else:
                api_url = f"https://fonts.googleapis.com/css2?family={font_name_encoded}:wght@{weight}&display=swap"

            # Use proper headers to get truetype format
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse CSS to find font file URL
            import re
            # Look for truetype format URLs
            font_urls = re.findall(r'src:\s*url\(([^)]+)\)\s+format\([\'"]truetype[\'"]\)', response.text)

            if not font_urls:
                # Try finding any URL in src
                font_urls = re.findall(r'src:\s*url\(([^)]+)\)', response.text)

            if font_urls:
                # Download the font file
                font_url = font_urls[0].strip()
                logger.info(f"Downloading {font_family} from CDN: {font_url[:50]}...")

                font_response = requests.get(font_url, timeout=15)
                font_response.raise_for_status()

                # Save to cache
                with open(font_path, 'wb') as f:
                    f.write(font_response.content)

                logger.info(f"Downloaded and cached Google Font: {font_family} ({style})")
                return str(font_path)
            else:
                logger.warning(f"No font URL found in CSS for {font_family}")

        except Exception as e:
            logger.warning(f"Could not download Google Font {font_family} ({style}): {e}")

        return None

    def get_font_file(self, style):
        """Get font filename based on style (bold, italic, normal) for Windows and Ubuntu."""
        # Windows fonts
        windows_fonts = {
            'bold': 'arialbd.ttf',
            'italic': 'ariali.ttf',
            'normal': 'arial.ttf'
        }

        # Ubuntu/Linux fonts (DejaVu Sans is pre-installed on most Linux systems)
        linux_fonts = {
            'bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            'italic': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf',
            'normal': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        }

        return {
            'windows': windows_fonts.get(style, 'arial.ttf'),
            'linux': linux_fonts.get(style, '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
        }

    def load_font_with_fallback(self, style, size, google_font_family=None):
        """Load font with Google Fonts support and fallback for Windows/Linux compatibility."""
        # Try Google Font first if specified
        if google_font_family:
            google_font_path = self.download_google_font(google_font_family, style)
            if google_font_path:
                try:
                    return ImageFont.truetype(google_font_path, size)
                except Exception as e:
                    logger.warning(f"Could not load Google Font: {e}")

        font_files = self.get_font_file(style)

        # Try Windows fonts
        try:
            return ImageFont.truetype(font_files['windows'], size)
        except:
            pass

        # Try Linux fonts
        try:
            return ImageFont.truetype(font_files['linux'], size)
        except:
            pass

        # Fallback to default
        logger.warning(f"Could not load {style} font, using default")
        return ImageFont.load_default()

    def try_load_fonts(self):
        """Load modern fonts with sizes and styles from Config."""
        try:
            # Load fonts based on configured styles with Google Fonts and OS fallback
            self.font_tag = self.load_font_with_fallback(self.font_tag_style, self.font_tag_size, self.font_tag_family)
            self.font_title = self.load_font_with_fallback(self.font_title_style, self.font_title_size, self.font_title_family)
            self.font_body = self.load_font_with_fallback(self.font_description_style, self.font_description_size, self.font_description_family)

            # Brand font - special handling for italic (cursive look)
            if self.font_brand_family:
                self.font_brand = self.load_font_with_fallback(self.font_brand_style, self.font_brand_size, self.font_brand_family)
            elif self.font_brand_style == 'italic':
                # Try cursive fonts
                cursive_fonts = [
                    "segoeui.ttf",  # Windows
                    "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",  # Ubuntu
                    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",  # Ubuntu fallback
                ]

                font_loaded = False
                for font_path in cursive_fonts:
                    try:
                        self.font_brand = ImageFont.truetype(font_path, self.font_brand_size)
                        font_loaded = True
                        break
                    except:
                        continue

                if not font_loaded:
                    self.font_brand = self.load_font_with_fallback('italic', self.font_brand_size)
            else:
                self.font_brand = self.load_font_with_fallback(self.font_brand_style, self.font_brand_size)
        except Exception as e:
            logger.warning(f"Error loading fonts: {e}, using defaults")
            default = ImageFont.load_default()
            self.font_title = self.font_body = self.font_tag = self.font_brand = default

    def create_gradient_background(self, height) -> Image:
        """Create modern gradient background with subtle accents."""
        img = Image.new('RGB', (self.width, height), self.bg_black)
        draw = ImageDraw.Draw(img)

        # Create subtle gradient from black to greyish black
        for y in range(height):
            alpha = y / height
            r = int(self.bg_black[0] + (self.bg_grey[0] - self.bg_black[0]) * alpha)
            g = int(self.bg_black[1] + (self.bg_grey[1] - self.bg_black[1]) * alpha)
            b = int(self.bg_black[2] + (self.bg_grey[2] - self.bg_black[2]) * alpha)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))

        # Add very subtle geometric accents
        overlay = Image.new('RGBA', (self.width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        # Subtle sky blue and light green glows
        overlay_draw.ellipse([100, 50, 350, 300], fill=self.sky_blue + (15,))
        overlay_draw.ellipse([self.width - 300, height - 250, self.width - 50, height - 50],
                            fill=self.light_green + (15,))

        overlay = overlay.filter(ImageFilter.GaussianBlur(60))
        img.paste(overlay, (0, 0), overlay)

        return img

    def draw_rounded_rect(self, draw, xy, radius, fill, outline=None, width=0):
        """Draw rounded rectangle."""
        x1, y1, x2, y2 = xy
        draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill, outline=outline, width=width)
        draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill, outline=outline, width=width)

        draw.ellipse([x1, y1, x1 + radius * 2, y1 + radius * 2], fill=fill, outline=outline)
        draw.ellipse([x2 - radius * 2, y1, x2, y1 + radius * 2], fill=fill, outline=outline)
        draw.ellipse([x1, y2 - radius * 2, x1 + radius * 2, y2], fill=fill, outline=outline)
        draw.ellipse([x2 - radius * 2, y2 - radius * 2, x2, y2], fill=fill, outline=outline)

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
        Generate enhanced modern news image with side-by-side layout.

        Args:
            title: News headline
            description: News description
            timestamp: Publication time (not displayed)
            image_url: Optional news image URL

        Returns:
            BytesIO containing PNG image
        """
        # Calculate required height based on content
        # First, calculate how much space we need
        temp_draw = ImageDraw.Draw(Image.new('RGB', (1, 1)))

        card_margin = 40
        left_padding = 50
        left_section_width = int((self.width - (card_margin * 2)) * 0.65)
        left_max_width = left_section_width - (left_padding * 2)

        # Calculate tag height
        tag_bbox = self.font_tag.getbbox("Live Market Updates")
        tag_height = tag_bbox[3] - tag_bbox[1]

        # Calculate title height
        title_lines = self.wrap_text(title, self.font_title, left_max_width)
        title_height = len(title_lines) * 78

        # Calculate description height (RESTORED)
        desc_height = 0
        if description:
            desc_lines = self.wrap_text(description, self.font_body, left_max_width)
            desc_height = len(desc_lines) * 64 + 30

        # Calculate total required height
        content_height = 50 + tag_height + 30 + 45 + title_height + desc_height + 100
        required_height = max(self.min_height, content_height + (card_margin * 2))

        # Create gradient background with dynamic height
        base = self.create_gradient_background(required_height)
        draw = ImageDraw.Draw(base)

        # Main content card
        card_margin = 40
        card_y1 = 50
        card_x1 = card_margin
        card_x2 = self.width - card_margin
        card_y2 = required_height - card_margin

        # Draw shadow
        shadow = Image.new('RGBA', (self.width, required_height), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        self.draw_rounded_rect(
            shadow_draw,
            [card_x1 + 8, card_y1 + 8, card_x2 + 8, card_y2 + 8],
            radius=25,
            fill=(0, 0, 0, 80)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(15))
        base.paste(shadow, (0, 0), shadow)

        # Draw white content card
        self.draw_rounded_rect(
            draw,
            [card_x1, card_y1, card_x2, card_y2],
            radius=25,
            fill=self.card_bg
        )

        # Divide card into left (text) and right (image) sections
        card_width = card_x2 - card_x1
        card_height = card_y2 - card_y1

        # Left section for text (65% width)
        left_section_width = int(card_width * 0.65)
        left_x1 = card_x1
        left_x2 = card_x1 + left_section_width

        # Right section for image (35% width)
        right_x1 = left_x2
        right_x2 = card_x2

        # LEFT SECTION: Live signal tag, Title and Description
        left_padding = 50
        left_content_x = left_x1 + left_padding
        left_max_width = left_section_width - (left_padding * 2)
        content_y = card_y1 + 50

        # Live Market Updates tag with dark gray background (from Config)
        tag_text = "Live Market Updates"
        tag_bbox = self.font_tag.getbbox(tag_text)
        tag_width = tag_bbox[2] - tag_bbox[0]
        tag_height = tag_bbox[3] - tag_bbox[1]

        # Tag background color from Config (dark gray)
        tag_padding_x = 25
        tag_padding_y = 15
        tag_x = left_content_x
        tag_y = content_y

        self.draw_rounded_rect(
            draw,
            [tag_x, tag_y, tag_x + tag_width + (tag_padding_x * 2),
             tag_y + tag_height + (tag_padding_y * 2)],
            radius=10,
            fill=self.tag_bg_color
        )

        draw.text(
            (tag_x + tag_padding_x, tag_y + tag_padding_y),
            tag_text,
            fill=self.tag_text_color,
            font=self.font_tag
        )

        content_y += tag_height + (tag_padding_y * 2) + 45

        # Title color from Config (dark blue) - SHOW ALL LINES
        for line in title_lines:
            draw.text((left_content_x, content_y), line, fill=self.title_color, font=self.font_title)
            content_y += 78

        # Description color from Config (dark gray) - SHOW ALL LINES (RESTORED)
        if description:
            content_y += 30
            desc_lines = self.wrap_text(description, self.font_body, left_max_width)

            for line in desc_lines:
                draw.text((left_content_x, content_y), line, fill=self.description_color, font=self.font_body)
                content_y += 64

        # RIGHT SECTION: News Image (no border, larger size)
        if image_url:
            news_img = self.download_image(image_url)
            if news_img:
                # Calculate size to fit right section with minimal padding for larger image
                img_padding = 25
                img_max_width = (right_x2 - right_x1) - (img_padding * 2)
                img_max_height = card_height - (img_padding * 2)

                # Maintain aspect ratio
                aspect = news_img.width / news_img.height
                if aspect > (img_max_width / img_max_height):
                    new_width = img_max_width
                    new_height = int(new_width / aspect)
                else:
                    new_height = img_max_height
                    new_width = int(new_height * aspect)

                news_img = news_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Center the image in right section
                img_x = right_x1 + img_padding + (img_max_width - new_width) // 2
                img_y = card_y1 + img_padding + (img_max_height - new_height) // 2

                # Rounded mask (no border)
                mask = Image.new('L', news_img.size, 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle(
                    [(0, 0), news_img.size],
                    radius=15,
                    fill=255
                )

                base.paste(news_img, (img_x, img_y), mask)

        # Decorative corner accents
        accent_size = 30
        # Top right - sky blue arc
        draw.arc([card_x2 - accent_size - 25, card_y1 + 25, card_x2 - 25, card_y1 + accent_size + 25],
                 270, 360, fill=self.sky_blue, width=5)
        # Bottom left - light green arc
        draw.arc([card_x1 + 25, card_y2 - accent_size - 25, card_x1 + accent_size + 25, card_y2 - 25],
                 90, 180, fill=self.light_green, width=5)

        # Save to BytesIO
        output = BytesIO()
        base.save(output, format='PNG', quality=95)
        output.seek(0)
        return output

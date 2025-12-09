"""
Premium Light Theme News Image Generator
Elegant, clean, and modern design with professional aesthetics
"""

import logging
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
from typing import Optional
import requests
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class EnhancedNewsImageGenerator:
    """Generates premium light-themed news images."""

    def __init__(self):
        """Initialize with premium design parameters."""
        self.width = 1200
        self.height = 675  # 16:9 aspect ratio

        # Premium Light Theme Color Palette
        self.bg_white = (255, 255, 255)
        self.bg_light = (248, 250, 252)  # Soft white
        self.accent_blue = (59, 130, 246)  # Bright blue
        self.accent_indigo = (99, 102, 241)  # Rich indigo
        self.text_dark = (15, 23, 42)  # Almost black
        self.text_gray = (71, 85, 105)  # Medium gray
        self.border_color = (226, 232, 240)  # Subtle border
        self.live_red = (239, 68, 68)  # Vibrant red for LIVE badge

        # Font sizes
        self.font_tag_size = 14
        self.font_title_size = 48
        self.font_description_size = 18
        
        self.try_load_fonts()

    def download_google_font(self, font_family, weight='400'):
        """Download Google Font."""
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

            headers = {'User-Agent': 'Mozilla/5.0'}
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

                return str(font_path)

        except Exception as e:
            logger.warning(f"Could not download font: {e}")

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
        """Load premium fonts."""
        try:
            # Use Inter font family for modern, clean look
            inter_regular = self.download_google_font('Inter', '400')
            inter_bold = self.download_google_font('Inter', '700')
            inter_semibold = self.download_google_font('Inter', '600')
            
            # Tag font
            if inter_semibold:
                self.font_tag = ImageFont.truetype(inter_semibold, self.font_tag_size)
                logger.info(f"Loaded Inter SemiBold for tags (size {self.font_tag_size})")
            elif inter_regular:
                self.font_tag = ImageFont.truetype(inter_regular, self.font_tag_size)
                logger.info(f"Loaded Inter Regular for tags (size {self.font_tag_size})")
            else:
                self.font_tag = self.load_system_font(self.font_tag_size)
                logger.info(f"Loaded system font for tags (size {self.font_tag_size})")
            
            # Title font
            if inter_bold:
                self.font_title = ImageFont.truetype(inter_bold, self.font_title_size)
                logger.info(f"Loaded Inter Bold for title (size {self.font_title_size})")
            else:
                self.font_title = self.load_system_font(self.font_title_size)
                logger.info(f"Loaded system font for title (size {self.font_title_size})")
            
            # Description font
            if inter_regular:
                self.font_body = ImageFont.truetype(inter_regular, self.font_description_size)
                logger.info(f"Loaded Inter Regular for body (size {self.font_description_size})")
            else:
                self.font_body = self.load_system_font(self.font_description_size)
                logger.info(f"Loaded system font for body (size {self.font_description_size})")
                
        except Exception as e:
            logger.warning(f"Error loading fonts: {e}")
            self.font_title = self.load_system_font(self.font_title_size)
            self.font_body = self.load_system_font(self.font_description_size)
            self.font_tag = self.load_system_font(self.font_tag_size)

    def create_modern_background(self) -> Image:
        """Create clean, premium light background."""
        # Start with pure white
        img = Image.new('RGB', (self.width, self.height), self.bg_white)
        
        # Add very subtle gradient overlay
        overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        
        # Soft top-to-bottom gradient
        for y in range(self.height):
            alpha = int(5 * (y / self.height))
            draw_overlay.line([(0, y), (self.width, y)], fill=(100, 116, 139, alpha))
        
        overlay = overlay.filter(ImageFilter.GaussianBlur(30))
        img.paste(overlay, (0, 0), overlay)
        
        # Add subtle colored accent in corner - very light
        accent = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        accent_draw = ImageDraw.Draw(accent)
        
        # Blue glow - top right
        accent_draw.ellipse([self.width - 400, -200, self.width + 100, 300], 
                           fill=(59, 130, 246, 12))
        
        accent = accent.filter(ImageFilter.GaussianBlur(120))
        img.paste(accent, (0, 0), accent)
        
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
        Generate premium light-themed news image.

        Args:
            title: News headline
            description: News description
            timestamp: Publication time
            image_url: Optional news image URL

        Returns:
            BytesIO containing PNG image
        """
        # Create background
        base = self.create_modern_background()
        draw = ImageDraw.Draw(base)
        
        # Layout parameters
        padding = 60
        content_y = 60
        
        # LIVE indicator
        live_x = padding
        live_y = content_y
        
        # Draw LIVE badge with glow
        glow = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse([live_x - 4, live_y - 4, live_x + 14, live_y + 14], 
                         fill=(239, 68, 68, 40))
        glow = glow.filter(ImageFilter.GaussianBlur(6))
        base.paste(glow, (0, 0), glow)
        
        # LIVE dot
        draw.ellipse([live_x, live_y, live_x + 10, live_y + 10], fill=self.live_red)
        
        # LIVE text
        draw.text((live_x + 18, live_y - 3), "LIVE", fill=self.live_red, font=self.font_tag)
        
        content_y += 50
        
        # Main content
        if image_url:
            # Split layout - text 60%, image 40%
            text_width = int(self.width * 0.58)
            text_max = text_width - padding * 2
            
            # Title
            title_y = content_y + 30
            title_lines = self.wrap_text(title, self.font_title, text_max)
            
            for line in title_lines[:2]:
                draw.text((padding, title_y), line, fill=self.text_dark, font=self.font_title)
                title_y += 60
            
            # Description
            if description:
                desc_y = title_y + 25
                desc_lines = self.wrap_text(description, self.font_body, text_max)
                
                for line in desc_lines[:4]:
                    draw.text((padding, desc_y), line, fill=self.text_gray, font=self.font_body)
                    desc_y += 28
            
            # Accent line
            line_y = self.height - 80
            draw.rectangle([padding, line_y, padding + 60, line_y + 3], fill=self.accent_blue)
            
            # Image on right
            news_img = self.download_image(image_url)
            if news_img:
                img_x = text_width + 20
                img_y = content_y + 10
                img_max_w = self.width - img_x - padding
                img_max_h = self.height - img_y - padding - 20
                
                # Resize maintaining aspect ratio
                aspect = news_img.width / news_img.height
                if aspect > (img_max_w / img_max_h):
                    new_w = img_max_w
                    new_h = int(new_w / aspect)
                else:
                    new_h = img_max_h
                    new_w = int(new_h * aspect)
                
                news_img = news_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Center vertically
                img_y = content_y + (img_max_h - new_h) // 2
                
                # Subtle shadow
                shadow = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow)
                shadow_draw.rounded_rectangle(
                    [(img_x - 1, img_y - 1), (img_x + new_w + 1, img_y + new_h + 1)],
                    radius=16,
                    fill=(0, 0, 0, 40)
                )
                shadow = shadow.filter(ImageFilter.GaussianBlur(10))
                base.paste(shadow, (0, 0), shadow)
                
                # Border
                border = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                border_draw = ImageDraw.Draw(border)
                border_draw.rounded_rectangle(
                    [(img_x - 2, img_y - 2), (img_x + new_w + 2, img_y + new_h + 2)],
                    radius=15,
                    outline=self.border_color,
                    width=2
                )
                base.paste(border, (0, 0), border)
                
                # Paste image with rounded corners
                mask = Image.new('L', news_img.size, 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.rounded_rectangle([(0, 0), news_img.size], radius=13, fill=255)
                base.paste(news_img, (img_x, img_y), mask)
        
        else:
            # Full width centered layout
            text_max = self.width - padding * 2
            
            # Title centered
            title_y = content_y + 80
            title_lines = self.wrap_text(title, self.font_title, text_max)
            
            for line in title_lines[:3]:
                bbox = self.font_title.getbbox(line)
                text_w = bbox[2] - bbox[0]
                x = (self.width - text_w) // 2
                draw.text((x, title_y), line, fill=self.text_dark, font=self.font_title)
                title_y += 60
            
            # Description centered
            if description:
                desc_y = title_y + 35
                desc_max = int(text_max * 0.75)
                desc_lines = self.wrap_text(description, self.font_body, desc_max)
                
                for line in desc_lines[:4]:
                    bbox = self.font_body.getbbox(line)
                    text_w = bbox[2] - bbox[0]
                    x = (self.width - text_w) // 2
                    draw.text((x, desc_y), line, fill=self.text_gray, font=self.font_body)
                    desc_y += 28
            
            # Centered accent line
            line_y = self.height - 100
            line_w = 80
            draw.rectangle([(self.width - line_w) // 2, line_y, 
                          (self.width + line_w) // 2, line_y + 3], 
                          fill=self.accent_indigo)
        
        # Save
        output = BytesIO()
        base.save(output, format='PNG', quality=95)
        output.seek(0)
        return output
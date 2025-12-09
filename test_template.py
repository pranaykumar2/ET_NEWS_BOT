"""
Test Script for Image Generator Templates
This script generates a sample news image to preview the template design.
Simply update IMAGE_GENERATOR_MODULE to test different templates.
"""

import os
import sys
from datetime import datetime

# ============================================================================
# CONFIGURATION - Update this to test different image generator templates
# ============================================================================
IMAGE_GENERATOR_MODULE = "image_generator_enhanced"  # Change this to test other templates
# ============================================================================

# Sample news data for testing
SAMPLE_DATA = {
    "title": "Tech Giants Rally as AI Boom Drives Market Sentiment Higher",
    "description": "Major ₹ &*^%$@! technology stocks surged today as investors showed renewed confidence in artificial intelligence capabilities. The rally was led by semiconductor manufacturers and cloud computing companies, with analysts citing strong quarterly earnings and positive guidance for the sector's continued growth.",
    "timestamp": datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"),
    "image_url": "https://img.etimg.com/thumb/msid-115839569,width-300,height-225,imgsize-33154,resizemode-75/markets/stocks/news/stock-radar-sun-pharma-stock-showing-signs-of-bottoming-out-near-rs-1730-on-daily-charts-time-to-buy.jpg"
}

def test_template():
    """Generate a sample image using the configured template."""
    try:
        print("=" * 70)
        print(f"Testing Image Template: {IMAGE_GENERATOR_MODULE}")
        print("=" * 70)
        
        # Dynamically import the image generator module
        print(f"\n[1/4] Importing module: {IMAGE_GENERATOR_MODULE}...")
        module = __import__(IMAGE_GENERATOR_MODULE)
        
        # Find the generator class (looks for classes ending with 'ImageGenerator')
        generator_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and 'ImageGenerator' in attr_name:
                generator_class = attr
                break
        
        if not generator_class:
            print(f"❌ Error: No ImageGenerator class found in {IMAGE_GENERATOR_MODULE}")
            return
        
        print(f"✓ Found generator class: {generator_class.__name__}")
        
        # Initialize the generator
        print(f"\n[2/4] Initializing {generator_class.__name__}...")
        generator = generator_class()
        print("✓ Generator initialized successfully")
        
        # Generate the image
        print(f"\n[3/4] Generating sample news image...")
        print(f"   Title: {SAMPLE_DATA['title'][:60]}...")
        print(f"   Description: {SAMPLE_DATA['description'][:80]}...")
        
        output = generator.generate_news_image(
            title=SAMPLE_DATA['title'],
            description=SAMPLE_DATA['description'],
            timestamp=SAMPLE_DATA['timestamp'],
            image_url=SAMPLE_DATA['image_url']
        )
        
        # Save the image
        output_filename = f"test_output_{IMAGE_GENERATOR_MODULE}.png"
        print(f"\n[4/4] Saving image to: {output_filename}...")
        
        with open(output_filename, 'wb') as f:
            f.write(output.getvalue())
        
        file_size = os.path.getsize(output_filename) / 1024  # KB
        
        print("✓" * 35)
        print(f"\n✅ SUCCESS! Template preview generated:")
        print(f"   📁 File: {output_filename}")
        print(f"   📊 Size: {file_size:.2f} KB")
        print(f"   🖼️  Open the file to preview the template design")
        print("\n" + "✓" * 35)
        
    except ImportError as e:
        print(f"\n❌ Error: Could not import '{IMAGE_GENERATOR_MODULE}'")
        print(f"   Make sure the file '{IMAGE_GENERATOR_MODULE}.py' exists")
        print(f"   Details: {e}")
    except AttributeError as e:
        print(f"\n❌ Error: The module doesn't have a 'generate_news_image' method")
        print(f"   Details: {e}")
    except Exception as e:
        print(f"\n❌ Error generating template preview:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def show_usage():
    """Show usage instructions."""
    print("\n" + "=" * 70)
    print("HOW TO USE THIS SCRIPT:")
    print("=" * 70)
    print("""
1. Edit this file (test_template.py)
2. Update IMAGE_GENERATOR_MODULE at the top to your template file name
   Example: IMAGE_GENERATOR_MODULE = "image_generator_v2"
3. Run: python test_template.py
4. Check the generated PNG file to preview your template

SAMPLE DATA USED:
- Tech news title about AI boom
- 2-3 sentence description
- Current timestamp
- Sample stock market image from Economic Times

You can modify SAMPLE_DATA dictionary to test with different content.
    """)
    print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Allow passing template name as command line argument
        IMAGE_GENERATOR_MODULE = sys.argv[1].replace('.py', '')
    
    if '--help' in sys.argv or '-h' in sys.argv:
        show_usage()
    else:
        test_template()
        print("\n💡 Tip: Run 'python test_template.py --help' for usage instructions")

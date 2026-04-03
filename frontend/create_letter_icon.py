from PIL import Image, ImageDraw, ImageFont
import os

def create_letter_icon(output_path):
    size = 1024
    # Create squircle mask
    mask = Image.new('L', (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rounded_rectangle((0, 0, size, size), radius=int(size * 0.225), fill=255)
    
    # Create background (vibrant gradient or solid color)
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    bg = Image.new('RGBA', (size, size), (49, 46, 129, 255)) # Deep Indigo
    
    # Draw text "IG"
    draw = ImageDraw.Draw(bg)
    try:
        # Try to use a nice system font if available
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 500)
    except:
        font = ImageFont.load_default()
        
    text = "IG"
    # Get text size to center it
    try:
        bbox = draw.textbbox((0,0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
    except:
        w, h = 400, 400
        
    x = (size - w) / 2
    y = (size - h) / 2 - 50 # Adjust vertical center
    
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    # Apply mask
    img.paste(bg, (0, 0), mask)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    print(f"Created letter icon at {output_path}")

create_letter_icon("build/icon.png")

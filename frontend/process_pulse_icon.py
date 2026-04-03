from PIL import Image, ImageChops, ImageDraw
import sys
import os

def process_icon(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return False
        
    try:
        # Open image
        img = Image.open(input_path).convert('RGBA')
        width, height = img.size
        
        # This image already has a squircle shape inside a white/transparent background.
        # We want to crop out the white border.
        
        # 1. Create a bounding box that slightly crops inward to remove any white artifacts
        # from the AI generation. Let's crop about 12% from each side since the squircle
        # in the generated image usually has some padding and a shadow.
        crop_margin_x = int(width * 0.11)
        crop_margin_y = int(height * 0.11)
        
        bbox = (
            crop_margin_x, 
            crop_margin_y, 
            width - crop_margin_x, 
            height - crop_margin_y
        )
        
        cropped = img.crop(bbox)
        
        # Make sure it's a perfect square
        size = max(cropped.size)
        square_img = cropped.resize((size, size), Image.LANCZOS)
        
        # 2. Apply a clean macOS squircle mask to ensure perfect corners
        # Apple's standard squircle radius is about 22.5% of the size
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        radius = int(size * 0.225)
        draw.rounded_rectangle((0, 0, size, size), radius=radius, fill=255)
        
        # 3. Create final image with transparent background and squircle mask
        final_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        final_img.paste(square_img, (0, 0), mask)
        
        # 4. Resize to 1024x1024 (Apple standard)
        final_img = final_img.resize((1024, 1024), Image.LANCZOS)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        final_img.save(output_path, 'PNG')
        print(f"Successfully processed pulse icon and saved to: {output_path}")
        return True
        
    except Exception as e:
        print(f"Error processing icon: {e}")
        return False

if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "raw_icon.png"
    output_file = "build/icon.png"
    process_icon(input_file, output_file)

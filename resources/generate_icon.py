#!/usr/bin/env python3
"""
Generate icon for QuickPdfOcr application
Creates a PNG icon representing PDF + OCR functionality
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon(size=256):
    """
    Create an icon for the QuickPdfOcr application
    
    Args:
        size (int): Size of the icon in pixels (width and height)
    
    Returns:
        Image: PIL Image object
    """
    # Create a new image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Colors
    document_color = (255, 255, 255, 255)  # White
    document_shadow = (100, 100, 100, 180)  # Gray shadow
    accent_color = (33, 150, 243, 255)  # Blue (Material Design blue)
    text_lines_color = (100, 100, 100, 255)  # Dark gray
    pdf_badge_color = (211, 47, 47, 255)  # Red for PDF
    
    # Calculate proportions
    margin = size * 0.1
    doc_width = size * 0.65
    doc_height = size * 0.75
    doc_left = (size - doc_width) / 2
    doc_top = (size - doc_height) / 2 + size * 0.05
    
    # Draw shadow for document
    shadow_offset = size * 0.02
    draw.rounded_rectangle(
        [doc_left + shadow_offset, doc_top + shadow_offset, 
         doc_left + doc_width + shadow_offset, doc_top + doc_height + shadow_offset],
        radius=size * 0.03,
        fill=document_shadow
    )
    
    # Draw main document
    draw.rounded_rectangle(
        [doc_left, doc_top, doc_left + doc_width, doc_top + doc_height],
        radius=size * 0.03,
        fill=document_color,
        outline=accent_color,
        width=int(size * 0.01)
    )
    
    # Draw text lines on document to represent content
    line_margin = size * 0.08
    line_spacing = size * 0.055
    line_width = doc_width * 0.7
    line_height = size * 0.015
    
    num_lines = 6
    for i in range(num_lines):
        y_pos = doc_top + line_margin + (i * line_spacing)
        # Vary line lengths slightly
        current_line_width = line_width * (0.9 if i == num_lines - 1 else 1.0)
        draw.rounded_rectangle(
            [doc_left + (doc_width - line_width) / 2, y_pos,
             doc_left + (doc_width - line_width) / 2 + current_line_width, y_pos + line_height],
            radius=line_height / 2,
            fill=text_lines_color
        )
    
    # Draw "PDF" badge in top-right corner
    badge_size = size * 0.25
    badge_left = doc_left + doc_width - badge_size - size * 0.02
    badge_top = doc_top - badge_size * 0.3
    
    # Badge circle background
    draw.ellipse(
        [badge_left, badge_top, badge_left + badge_size, badge_top + badge_size],
        fill=pdf_badge_color
    )
    
    # Try to use a nice font, fall back to default if not available
    try:
        # Try to load a bold font for the badge text
        font_size = int(badge_size * 0.4)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        try:
            # Fallback to default font
            font = ImageFont.load_default()
        except:
            font = None
    
    # Draw "PDF" text on badge
    badge_text = "PDF"
    if font:
        # Get text bounding box to center it
        bbox = draw.textbbox((0, 0), badge_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = badge_left + (badge_size - text_width) / 2
        text_y = badge_top + (badge_size - text_height) / 2 - bbox[1]
        draw.text((text_x, text_y), badge_text, fill=(255, 255, 255, 255), font=font)
    else:
        # If font loading failed, just put text without precise centering
        text_x = badge_left + badge_size * 0.25
        text_y = badge_top + badge_size * 0.35
        draw.text((text_x, text_y), badge_text, fill=(255, 255, 255, 255))
    
    # Draw scanning effect (diagonal lines to represent OCR scanning)
    scan_line_color = (33, 150, 243, 150)  # Semi-transparent blue
    scan_line_width = int(size * 0.008)
    
    # Draw 3 scanning lines
    for i in range(3):
        y_offset = doc_top + doc_height * 0.45 + (i * size * 0.08)
        # Draw horizontal scanning line
        draw.line(
            [doc_left, y_offset, doc_left + doc_width, y_offset],
            fill=scan_line_color,
            width=scan_line_width
        )
        # Draw small arrows on the right to show movement
        arrow_size = size * 0.03
        draw.polygon(
            [
                (doc_left + doc_width, y_offset),
                (doc_left + doc_width - arrow_size, y_offset - arrow_size / 2),
                (doc_left + doc_width - arrow_size, y_offset + arrow_size / 2)
            ],
            fill=scan_line_color
        )
    
    return img


def main():
    """Generate all required icon sizes"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Generate main icon at 256x256
    print("Generating icon at 256x256...")
    icon_256 = create_icon(256)
    icon_path_256 = os.path.join(script_dir, "icon.png")
    icon_256.save(icon_path_256, "PNG")
    print(f"Saved: {icon_path_256}")
    
    # Generate additional sizes for better scaling
    sizes = [16, 32, 48, 64, 128, 256, 512]
    print(f"\nGenerating multi-size icons for .ico file: {sizes}")
    
    # Create ICO file with multiple sizes
    ico_images = []
    for size in sizes:
        print(f"  - {size}x{size}")
        img = create_icon(size)
        ico_images.append(img)
    
    ico_path = os.path.join(script_dir, "icon.ico")
    ico_images[0].save(
        ico_path,
        format='ICO',
        sizes=[(s, s) for s in sizes]
    )
    print(f"Saved: {ico_path}")
    
    # For macOS, we need .icns format which requires iconutil or external tools
    # We'll create a high-res PNG that can be converted to .icns later
    print("\nGenerating high-resolution PNG for macOS .icns conversion...")
    icon_512 = create_icon(512)
    icon_path_512 = os.path.join(script_dir, "icon_512.png")
    icon_512.save(icon_path_512, "PNG")
    print(f"Saved: {icon_path_512}")
    
    print("\n✅ Icon generation complete!")
    print(f"   - icon.png (256x256) - Standard icon")
    print(f"   - icon.ico (multi-size) - Windows icon")
    print(f"   - icon_512.png (512x512) - High-res for macOS")
    print("\nFor macOS .icns, you can use: png2icns icon.icns icon_512.png")
    print("Or use iconutil on macOS with an iconset directory")


if __name__ == "__main__":
    main()

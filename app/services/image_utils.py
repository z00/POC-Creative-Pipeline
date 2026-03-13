import os

from PIL import Image, ImageDraw, ImageFont, ImageOps

ASPECT_RATIOS = {
    "1_1": (1080, 1080),  # Instagram Post
    "9_16": (1080, 1920),  # Stories / Reels
    "16_9": (1920, 1080),  # YouTube / Twitter
}


def create_variations(
    base_image_path: str, message: str, product_name: str, output_dir: str
) -> list:
    """
    Resizes image using 'Contain' logic within a usable area to ensure
    perfect centering above the text banner.
    """
    generated_files = []
    banner_height = 200

    with Image.open(base_image_path) as raw_img:
        # 1. Normalize to RGB (Handles PNG transparency by placing it on white)
        img_to_process = Image.new("RGB", raw_img.size, (255, 255, 255))
        if raw_img.mode == "RGBA":
            img_to_process.paste(raw_img, mask=raw_img.split()[3])
        else:
            img_to_process.paste(raw_img.convert("RGB"))

        for ratio_name, (target_w, target_h) in ASPECT_RATIOS.items():
            # 2. Calculate Usable Area (Total height minus the banner)
            usable_h = target_h - banner_height

            # 3. Create a white background for the product area
            # We use ImageOps.pad with (0.5, 0.5) for mathematical centering
            content_area = ImageOps.pad(
                img_to_process,
                (target_w, usable_h),
                color=(255, 255, 255),
                centering=(0.5, 0.5),
            )

            # 4. Assemble the final canvas
            # Create full-size white image and paste the centered content at the top
            final_img = Image.new("RGB", (target_w, target_h), (255, 255, 255))
            final_img.paste(content_area, (0, 0))

            # 5. Draw Black Banner at the bottom
            draw = ImageDraw.Draw(final_img)
            draw.rectangle(
                ((0, target_h - banner_height), (target_w, target_h)), fill="black"
            )

            # 6. Text Overlay Logic
            try:
                # Use a standard font; size 40 is a safe bet for 1080px widths
                font = ImageFont.truetype("arial.ttf", 45)
            except Exception:
                font = ImageFont.load_default()

            # Wrapping Logic
            margin = 60
            max_width = target_w - (margin * 2)
            words = message.split()
            lines = []

            while words:
                line = ""
                while (
                    words
                    and draw.textbbox((0, 0), line + words[0], font=font)[2] < max_width
                ):
                    line += words.pop(0) + " "
                lines.append(line.strip())

            # Draw up to 3 lines of text inside the banner
            # Offset y to vertically center text within the 200px banner
            y_text = target_h - (banner_height - 50)
            for line in lines[:3]:
                draw.text((margin, y_text), line, fill="white", font=font)
                y_text += 55

            # 7. Save Result
            safe_prod_name = product_name.replace(" ", "_").lower()
            filename = f"{safe_prod_name}_{ratio_name}.jpg"
            save_path = os.path.join(output_dir, filename)

            final_img.save(save_path, "JPEG", quality=95)
            generated_files.append(save_path)

    return generated_files

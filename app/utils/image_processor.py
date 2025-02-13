from PIL import Image
from io import BytesIO
import uuid
import os

UPLOAD_FOLDER = "app/web/static/uploads/"
WIDTH, HEIGHT = 600, 600  # Max size

def preprocess_image(image):
    """Processes an image (resize, crop, and convert to WEBP)."""
    img = Image.open(image.file)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.thumbnail((WIDTH, HEIGHT))

    # Cropping Logic
    cur_w, cur_h = img.size
    img_ratio = round(cur_w / cur_h, 2)

    if img_ratio < 0.8:  # Vertical cropping
        cr_size = (cur_h - cur_w) / 2.2
        top, bottom = cr_size, cur_h - cr_size
        img = img.crop((0, top, cur_w, bottom))

    elif img_ratio > 1.6:  # Horizontal cropping
        cr_size = (cur_w - cur_h) / 2.7
        left, right = cr_size, cur_w - cr_size
        img = img.crop((left, 0, right, cur_h))

    # Save the processed image as WEBP
    buffer = BytesIO()
    img.save(buffer, format="WEBP", optimize=True)
    buffer.seek(0)

    # Generate Unique Filename
    new_img_filename = f"{uuid.uuid4().hex}.webp"
    save_path = os.path.join(UPLOAD_FOLDER, new_img_filename)

    # Write to File
    with open(save_path, "wb") as f:
        f.write(buffer.getbuffer())

    return save_path.replace("app/web/", "")
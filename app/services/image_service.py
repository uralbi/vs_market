from PIL import Image
from io import BytesIO
import uuid
from fastapi import UploadFile
from app.utils.image_processor import preprocess_image
import os


class ImageService:
    def __init__(self):
        pass
        # os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    async def process_and_store_image(self, image: UploadFile) -> str:
        """
        Resize and optimize image before saving.
        """
        filepath = preprocess_image(image)
        return filepath

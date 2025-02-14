import os
from app.infra.database.models import ProductImageModel


def delete_images_from_disk(image_paths):
    """
    Delete images from disk given a list of image paths.
    """
    for image in image_paths:
        if isinstance(image, ProductImageModel):  # ✅ Ensure it's the correct type
            image_path = image.image_url  # ✅ Extract image path
        else:
            image_path = image  # Already a string

        full_path = os.path.join("app/web", image_path)  # ✅ Convert DB path to real path

        if os.path.exists(full_path):
            os.remove(full_path)
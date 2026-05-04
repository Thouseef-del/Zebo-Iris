# backend/services/image_saver.py

import os
import cv2
from datetime import datetime
from config import Config


class ImageSaver:
    """Save captured iris images to disk for auditing / debugging."""

    def __init__(self, save_dir=None):
        self.save_dir = save_dir or Config.IMAGE_SAVE_DIR
        os.makedirs(self.save_dir, exist_ok=True)

    def save_image(self, image, prefix="iris"):
        """
        Save a grayscale or BGR image and return the file path.
        """
        if image is None or image.size == 0:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{prefix}_{timestamp}.png"
        filepath = os.path.join(self.save_dir, filename)

        cv2.imwrite(filepath, image)
        return filepath

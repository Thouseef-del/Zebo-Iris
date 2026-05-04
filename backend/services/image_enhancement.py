# backend/services/image_enhancement.py

"""
Aggressive multi-stage denoising pipeline designed for noisy mobile camera
iris images.  Order: bilateral filter → CLAHE → non-local-means → normalise.
"""

import cv2
import numpy as np


class ImageEnhancer:
    """Enhance an iris image captured by a mobile phone camera."""

    def enhance(self, image):
        """
        Apply a pipeline optimised for mobile sensor noise:
        1. Bilateral filter   — edge-preserving smoothing
        2. CLAHE              — adaptive contrast (handles uneven mobile lighting)
        3. Non-local means    — state-of-art denoising without blurring texture
        4. Intensity normalisation to [0, 255]
        """
        if image is None or image.size == 0:
            return None

        # Ensure grayscale
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 1. Bilateral filter — removes noise while keeping iris texture edges
        #    d=9: neighbourhood diameter
        #    sigmaColor=75:  colour-space filter sigma
        #    sigmaSpace=75:  coordinate-space filter sigma
        filtered = cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)

        # 2. CLAHE — higher clipLimit for mobile's uneven illumination
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(filtered)

        # 3. Non-Local Means Denoising — gold standard for removing sensor noise
        #    h=10: filter strength (higher = more denoising)
        #    templateWindowSize=7, searchWindowSize=21
        denoised = cv2.fastNlMeansDenoising(
            enhanced, None, h=10, templateWindowSize=7, searchWindowSize=21
        )

        # 4. Normalise to full [0, 255] range
        normalised = cv2.normalize(denoised, None, 0, 255, cv2.NORM_MINMAX)

        return normalised

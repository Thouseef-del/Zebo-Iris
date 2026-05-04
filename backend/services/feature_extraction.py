# backend/services/feature_extraction.py
# DEPRECATED: Use iris_code_generator.py for binary iris code generation.
# This file is kept for backward compatibility but is no longer used.

import cv2
import numpy as np


class FeatureExtractor:

    def __init__(self, size=(64, 64)):
        self.size = size

    def preprocess(self, image):
        resized = cv2.resize(image, self.size)
        normalized = resized / 255.0
        return normalized

    def extract_features(self, image):
        processed = self.preprocess(image)
        feature_vector = processed.flatten()
        return feature_vector.tolist()
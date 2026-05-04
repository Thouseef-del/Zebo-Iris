# backend/services/duplicate_checker.py

import numpy as np
from services.hamming_matcher import HammingMatcher
from config import Config


class DuplicateChecker:
    """Check if an iris code already exists in the database before registration.
    Uses rotation-compensated, mask-aware Hamming matching."""

    def __init__(self, user_model, threshold=None):
        self.user_model = user_model
        self.threshold = threshold or Config.DUPLICATE_THRESHOLD
        self.matcher = HammingMatcher(user_model, threshold=self.threshold)

    def is_duplicate(self, input_code, input_mask=None):
        """
        Return True if the input iris code matches any stored code
        within the duplicate threshold (stricter than match threshold).
        Uses rotation-compensated matching for robustness.
        """
        users = self.user_model.get_all_iris_codes()

        for user in users:
            stored_code = user.get("iris_code")
            if not stored_code:
                continue

            stored_mask = user.get("noise_mask")

            distance = self.matcher.hamming_distance_rotated(
                input_code, stored_code, input_mask, stored_mask
            )

            if distance < self.threshold:
                return True

        return False
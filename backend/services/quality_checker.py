# backend/services/quality_checker.py

"""
Image quality assessment for mobile-captured iris images.

Rejects images that are too blurry, over/under-exposed, or have specular
reflections — all common with mobile phone cameras.
"""

import cv2
import numpy as np
from config import Config


class QualityChecker:
    """Gate-keep images before iris code generation to avoid garbage templates."""

    def __init__(self):
        self.blur_threshold = Config.QUALITY_BLUR_THRESHOLD
        self.min_iris_visible = Config.QUALITY_MIN_IRIS_VISIBLE
        self.brightness_low = Config.QUALITY_BRIGHTNESS_LOW
        self.brightness_high = Config.QUALITY_BRIGHTNESS_HIGH

    # --------------------------------------------------
    # Main entry point
    # --------------------------------------------------
    def assess(self, eye_image):
        """
        Run all quality checks on a grayscale eye image.

        Returns
        -------
        dict
            {
                "passed": bool,
                "score": float (0–100),
                "issues": list[str],
                "details": dict
            }
        """
        if eye_image is None or eye_image.size == 0:
            return {
                "passed": False,
                "score": 0.0,
                "issues": ["Empty image"],
                "details": {},
            }

        # Ensure grayscale
        if len(eye_image.shape) == 3:
            eye_image = cv2.cvtColor(eye_image, cv2.COLOR_BGR2GRAY)

        issues = []
        details = {}

        # --- 1. Blur / sharpness ---
        sharpness = self._sharpness_score(eye_image)
        details["sharpness"] = round(sharpness, 2)
        if sharpness < self.blur_threshold:
            issues.append(
                f"Image too blurry (sharpness {sharpness:.1f}, need ≥{self.blur_threshold})"
            )

        # --- 2. Brightness / exposure ---
        mean_brightness = float(np.mean(eye_image))
        details["mean_brightness"] = round(mean_brightness, 2)
        if mean_brightness < self.brightness_low:
            issues.append(
                f"Image too dark (brightness {mean_brightness:.0f}, need ≥{self.brightness_low})"
            )
        elif mean_brightness > self.brightness_high:
            issues.append(
                f"Image overexposed (brightness {mean_brightness:.0f}, need ≤{self.brightness_high})"
            )

        # --- 3. Specular reflection ---
        reflection_ratio = self._specular_ratio(eye_image)
        details["specular_ratio"] = round(reflection_ratio, 4)
        if reflection_ratio > 0.05:
            issues.append(
                f"Specular reflection detected ({reflection_ratio*100:.1f}% saturated pixels)"
            )

        # --- 4. Contrast ---
        contrast = float(np.std(eye_image))
        details["contrast_std"] = round(contrast, 2)
        if contrast < 15.0:
            issues.append(
                f"Very low contrast (std {contrast:.1f}), iris texture may be unreadable"
            )

        # Compute overall score (0–100)
        score = self._compute_score(sharpness, mean_brightness, contrast, reflection_ratio)
        details["score"] = round(score, 2)

        return {
            "passed": len(issues) == 0,
            "score": round(score, 2),
            "issues": issues,
            "details": details,
        }

    # --------------------------------------------------
    # Iris-visible fraction (used after segmentation)
    # --------------------------------------------------
    def check_iris_visibility(self, noise_mask):
        """
        Given a noise mask (1 = valid, 0 = occluded/invalid),
        check that enough iris texture is visible.
        """
        if noise_mask is None or noise_mask.size == 0:
            return True  # no mask means assume all visible

        visible = float(np.mean(noise_mask))
        if visible < self.min_iris_visible:
            return False
        return True

    # --------------------------------------------------
    # Internal helpers
    # --------------------------------------------------
    @staticmethod
    def _sharpness_score(gray):
        """Laplacian variance — higher = sharper."""
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        return float(lap.var())

    @staticmethod
    def _specular_ratio(gray):
        """Fraction of near-saturated pixels (>250)."""
        saturated = np.sum(gray > 250)
        return float(saturated) / gray.size

    @staticmethod
    def _compute_score(sharpness, brightness, contrast, reflection):
        """Weighted quality score in [0, 100]."""
        # Sharpness component (0–40)
        s = min(sharpness / 200.0, 1.0) * 40.0

        # Brightness component (0–20) — penalise extremes
        if 60 <= brightness <= 180:
            b = 20.0
        elif 40 <= brightness <= 220:
            b = 12.0
        else:
            b = 0.0

        # Contrast component (0–25)
        c = min(contrast / 50.0, 1.0) * 25.0

        # Reflection penalty (0–15, 15 = no reflection)
        r = max(0.0, (1.0 - reflection * 10)) * 15.0

        return s + b + c + r

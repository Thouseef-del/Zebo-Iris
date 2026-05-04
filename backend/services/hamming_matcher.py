# backend/services/hamming_matcher.py

"""
Rotation-compensated Hamming distance matcher with noise-mask support.

Mobile camera iris codes are cyclically shift-invariant along the θ axis.
When the user tilts their head, the normalized iris strip shifts circularly.
We try ±N cyclic bit-shifts and take the minimum Hamming distance to
compensate for up to ±N×(360°/code_width) degrees of head tilt.
"""

import numpy as np
from config import Config


class HammingMatcher:
    """Match an input iris code against stored templates using
    rotation-compensated, mask-aware Hamming Distance."""

    def __init__(self, user_model, threshold=None):
        self.user_model = user_model
        self.threshold = threshold or Config.HAMMING_MATCH_THRESHOLD
        self.rotation_shifts = Config.ROTATION_SHIFTS
        self.code_height, self.code_width = Config.IRIS_CODE_SIZE

    # --------------------------------------------------
    # Core: mask-aware Hamming Distance with rotation
    # --------------------------------------------------
    @staticmethod
    def hamming_distance(code1, code2, mask1=None, mask2=None):
        """
        Compute the normalised Hamming distance between two binary codes,
        optionally excluding bits marked as invalid by noise masks.

        Parameters
        ----------
        code1, code2 : list or np.ndarray  — binary iris codes (0s and 1s)
        mask1, mask2 : list or np.ndarray or None — noise masks (1 = valid, 0 = invalid)

        Returns
        -------
        float in [0, 1] where 0 = identical, 0.5 = random
        """
        a = np.array(code1, dtype=np.int8)
        b = np.array(code2, dtype=np.int8)

        # Truncate to the shorter length
        min_len = min(len(a), len(b))
        a = a[:min_len]
        b = b[:min_len]

        if min_len == 0:
            return 1.0

        # Build combined valid-bit mask
        if mask1 is not None and mask2 is not None:
            m1 = np.array(mask1, dtype=np.int8)[:min_len]
            m2 = np.array(mask2, dtype=np.int8)[:min_len]
            valid = m1 & m2  # both must be valid
        elif mask1 is not None:
            valid = np.array(mask1, dtype=np.int8)[:min_len]
        elif mask2 is not None:
            valid = np.array(mask2, dtype=np.int8)[:min_len]
        else:
            valid = None

        if valid is not None:
            valid_count = int(np.sum(valid))
            if valid_count == 0:
                return 1.0
            disagreements = int(np.sum((a != b) & (valid == 1)))
            return float(disagreements) / valid_count
        else:
            return float(np.sum(a != b)) / min_len

    # --------------------------------------------------
    # Rotation-compensated Hamming distance
    # --------------------------------------------------
    def hamming_distance_rotated(self, code1, code2, mask1=None, mask2=None):
        """
        Try ±self.rotation_shifts cyclic bit-shifts and return the
        minimum Hamming distance across all rotations.

        The iris code is treated as a 2D array (height × width) and
        shifted circularly along the width (θ) axis.
        """
        a = np.array(code1, dtype=np.int8)
        b = np.array(code2, dtype=np.int8)

        min_len = min(len(a), len(b))
        a = a[:min_len]
        b = b[:min_len]

        # Determine the 2D shape for cyclic shifting
        expected_len = self.code_height * self.code_width
        n_filters = min_len // expected_len if expected_len > 0 else 1

        if n_filters < 1 or expected_len == 0:
            # Can't reshape — fall back to non-rotated
            return self.hamming_distance(code1, code2, mask1, mask2)

        total_len = n_filters * expected_len
        a = a[:total_len]
        b = b[:total_len]

        # Reshape to (n_filters * height, width) for circular shifting
        a_2d = a.reshape(-1, self.code_width)
        b_2d = b.reshape(-1, self.code_width)

        # Handle masks
        m1_2d = None
        m2_2d = None
        if mask1 is not None:
            m1 = np.array(mask1, dtype=np.int8)[:total_len]
            # Noise mask is per-pixel on the normalised strip, tile across filters
            base_mask_len = self.code_height * self.code_width
            if len(m1) == base_mask_len:
                m1 = np.tile(m1, n_filters)
            m1_2d = m1[:total_len].reshape(-1, self.code_width)
        if mask2 is not None:
            m2 = np.array(mask2, dtype=np.int8)[:total_len]
            base_mask_len = self.code_height * self.code_width
            if len(m2) == base_mask_len:
                m2 = np.tile(m2, n_filters)
            m2_2d = m2[:total_len].reshape(-1, self.code_width)

        best_distance = 1.0

        for shift in range(-self.rotation_shifts, self.rotation_shifts + 1):
            # Cyclic-shift b along the width (θ) axis
            b_shifted = np.roll(b_2d, shift, axis=1)

            m2_shifted = None
            if m2_2d is not None:
                m2_shifted = np.roll(m2_2d, shift, axis=1)

            # Compute mask-aware Hamming on flattened arrays
            dist = self.hamming_distance(
                a_2d.flatten().tolist(),
                b_shifted.flatten().tolist(),
                m1_2d.flatten().tolist() if m1_2d is not None else None,
                m2_shifted.flatten().tolist() if m2_shifted is not None else None,
            )

            if dist < best_distance:
                best_distance = dist

        return best_distance

    # --------------------------------------------------
    # Find best match in database
    # --------------------------------------------------
    def find_match(self, input_code, input_mask=None):
        """
        Compare input_code against every stored iris code using
        rotation-compensated, mask-aware Hamming distance.
        Return the best match if below threshold, else 'No Match Found'.
        """
        users = self.user_model.get_all_iris_codes()

        best_match = None
        best_distance = 1.0

        for user in users:
            stored_code = user.get("iris_code")
            if not stored_code:
                continue

            stored_mask = user.get("noise_mask")

            distance = self.hamming_distance_rotated(
                input_code, stored_code, input_mask, stored_mask
            )

            if distance < best_distance:
                best_distance = distance
                best_match = user

        if best_match is not None and best_distance < self.threshold:
            confidence = round((1.0 - best_distance) * 100, 2)
            return {
                "status": "Match Found",
                "confidence_score": confidence,
                "hamming_distance": round(best_distance, 4),
                "data": {
                    "name": best_match.get("name"),
                    "address": best_match.get("address"),
                    "phone_no": best_match.get("phone_no"),
                    "relationship": best_match.get("relationship"),
                },
            }

        return {
            "status": "No Match Found",
            "message": "No matching iris found in database",
        }

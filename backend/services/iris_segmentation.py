# backend/services/iris_segmentation.py

"""
Iris segmentation with true Daugman rubber-sheet normalisation and
eyelid/eyelash occlusion masking.

The rubber-sheet unwrap maps the annular iris from polar (r, θ) coordinates
to a fixed-size rectangular strip, making the iris code invariant to pupil
dilation and centre shift — the single biggest accuracy gain for mobile
camera images.
"""

import cv2
import numpy as np


class IrisSegmentation:
    """Locates the pupil and iris boundaries in an eye image,
    masks eyelid occlusions, and performs Daugman-style rubber-sheet
    normalisation."""

    # --------------------------------------------------
    # 1. Segment the iris annular region
    # --------------------------------------------------
    def segment_iris(self, eye_image):
        """
        Detect the pupil and iris circles.
        Returns (iris_region_crop, pupil_centre, pupil_radius, iris_radius)
        or None on failure.

        The raw cropped region is still returned for backward-compatibility,
        but the key information is the circle parameters — used by
        `normalize_iris` for the polar unwrap.
        """
        if eye_image is None or eye_image.size == 0:
            return None

        # Ensure grayscale
        if len(eye_image.shape) == 3:
            eye_image = cv2.cvtColor(eye_image, cv2.COLOR_BGR2GRAY)

        h, w = eye_image.shape

        # --- Detect pupil circle ---
        pupil_info = self._detect_pupil(eye_image)

        if pupil_info is None:
            # Fallback: assume pupil is roughly centred
            cx, cy = w // 2, h // 2
            r_pupil = min(h, w) // 6
        else:
            cx, cy, r_pupil = pupil_info

        # Iris radius is roughly 2–3× the pupil radius
        r_iris = min(int(r_pupil * 2.5), min(h, w) // 2)

        # Store circle params for use by normalize_iris
        self._last_params = {
            "eye_image": eye_image,
            "cx": cx,
            "cy": cy,
            "r_pupil": r_pupil,
            "r_iris": r_iris,
        }

        # Create a mask for the iris annulus
        mask = np.zeros_like(eye_image)
        cv2.circle(mask, (cx, cy), r_iris, 255, -1)
        cv2.circle(mask, (cx, cy), r_pupil, 0, -1)

        iris_region = cv2.bitwise_and(eye_image, mask)

        # Crop to bounding box of the iris circle
        x1 = max(cx - r_iris, 0)
        y1 = max(cy - r_iris, 0)
        x2 = min(cx + r_iris, w)
        y2 = min(cy + r_iris, h)

        cropped = iris_region[y1:y2, x1:x2]

        if cropped.size == 0:
            return None

        return cropped

    # --------------------------------------------------
    # 2. True Daugman rubber-sheet normalisation
    # --------------------------------------------------
    def normalize_iris(self, iris_region, output_size=(64, 512)):
        """
        Rubber-sheet (Daugman-style) polar normalisation.

        Unwraps the annular iris region from (r, θ) polar coordinates
        into a rectangular (rows × cols) strip using bilinear interpolation.

        Also generates a noise mask (1 = valid pixel, 0 = invalid/occluded).

        Parameters
        ----------
        iris_region : np.ndarray
            The cropped iris image (used as fallback for dimensions).
        output_size : tuple
            (rows, cols) of the normalised output strip.

        Returns
        -------
        tuple (normalised_strip, noise_mask)
            normalised_strip : np.ndarray of shape output_size
            noise_mask : np.ndarray of shape output_size (uint8, 0 or 1)
        """
        nrows, ncols = output_size

        # Use stored circle parameters from segment_iris
        params = getattr(self, "_last_params", None)

        if params is None:
            # Fallback: simple resize (backward-compatible)
            if iris_region is None or iris_region.size == 0:
                return None, None
            resized = cv2.resize(iris_region, (ncols, nrows))
            mask = np.ones((nrows, ncols), dtype=np.uint8)
            return resized, mask

        eye_image = params["eye_image"]
        cx = params["cx"]
        cy = params["cy"]
        r_pupil = params["r_pupil"]
        r_iris = params["r_iris"]
        h, w = eye_image.shape[:2]

        # --- Detect eyelid occlusion mask on the original eye image ---
        occlusion_mask = self._detect_eyelid_mask(eye_image, cx, cy, r_iris)

        # --- Polar unwrap ---
        normalised = np.zeros((nrows, ncols), dtype=np.uint8)
        noise_mask = np.ones((nrows, ncols), dtype=np.uint8)

        theta_values = np.linspace(0, 2 * np.pi, ncols, endpoint=False)
        r_values = np.linspace(0.0, 1.0, nrows)  # 0 = pupil boundary, 1 = iris boundary

        for j, theta in enumerate(theta_values):
            cos_t = np.cos(theta)
            sin_t = np.sin(theta)

            for i, r_frac in enumerate(r_values):
                # Map from normalised (r, θ) to pixel coordinates
                r = r_pupil + r_frac * (r_iris - r_pupil)
                px = cx + r * cos_t
                py = cy + r * sin_t

                # Bounds check
                ix = int(round(px))
                iy = int(round(py))

                if 0 <= ix < w and 0 <= iy < h:
                    normalised[i, j] = eye_image[iy, ix]

                    # Check occlusion mask
                    if occlusion_mask[iy, ix] == 0:
                        noise_mask[i, j] = 0
                else:
                    # Out of bounds → mark as noise
                    noise_mask[i, j] = 0
                    normalised[i, j] = 0

        return normalised, noise_mask

    # --------------------------------------------------
    # 3. Eyelid / eyelash occlusion detection
    # --------------------------------------------------
    def _detect_eyelid_mask(self, eye_image, cx, cy, r_iris):
        """
        Create a binary mask where 1 = iris texture visible, 0 = occluded
        by eyelid or eyelash.

        Uses horizontal edge detection in the upper/lower portions of the
        eye region to approximate eyelid boundaries.
        """
        h, w = eye_image.shape[:2]
        mask = np.ones((h, w), dtype=np.uint8)

        # Define upper and lower search regions (top/bottom 40% of eye region)
        y_top = max(cy - r_iris, 0)
        y_bot = min(cy + r_iris, h)
        y_mid = cy

        # --- Upper eyelid detection ---
        upper_region = eye_image[y_top:y_mid, :]
        if upper_region.size > 0:
            # Horizontal Sobel to find strong horizontal edges (eyelid boundary)
            sobel = cv2.Sobel(upper_region, cv2.CV_64F, 0, 1, ksize=3)
            abs_sobel = np.abs(sobel)

            # Find rows with strong horizontal edges
            row_energy = np.mean(abs_sobel, axis=1)
            threshold = np.mean(row_energy) + 3.0 * np.std(row_energy)

            # The eyelid edge is the strongest horizontal edge from the top
            strong_rows = np.where(row_energy > threshold)[0]
            if len(strong_rows) > 0:
                eyelid_row = strong_rows[-1]  # lowest strong edge in upper region
                mask[y_top:y_top + eyelid_row, :] = 0

        # --- Lower eyelid detection ---
        lower_region = eye_image[y_mid:y_bot, :]
        if lower_region.size > 0:
            sobel = cv2.Sobel(lower_region, cv2.CV_64F, 0, 1, ksize=3)
            abs_sobel = np.abs(sobel)

            row_energy = np.mean(abs_sobel, axis=1)
            threshold = np.mean(row_energy) + 3.0 * np.std(row_energy)

            strong_rows = np.where(row_energy > threshold)[0]
            if len(strong_rows) > 0:
                eyelid_row = strong_rows[0]  # highest strong edge in lower region
                mask[y_mid + eyelid_row:y_bot, :] = 0

        # --- Eyelash detection (high-frequency dark streaks) ---
        # Eyelashes appear as thin dark vertical/diagonal lines
        blurred = cv2.GaussianBlur(eye_image, (5, 5), 0)
        diff = cv2.absdiff(eye_image, blurred)

        # Eyelashes create high differences and are dark
        eyelash_mask = (diff > 35) & (eye_image < 50)
        mask[eyelash_mask] = 0

        return mask

    # --------------------------------------------------
    # 4. Pupil detection (improved for mobile images)
    # --------------------------------------------------
    def _detect_pupil(self, gray):
        """
        Detect the pupil circle using HoughCircles with adaptive
        thresholding fallback for noisy mobile images.
        Returns (cx, cy, radius) or None.
        """
        h, w = gray.shape

        # --- Primary: HoughCircles ---
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)

        min_radius = max(int(min(h, w) * 0.08), 5)
        max_radius = int(min(h, w) * 0.4)

        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=max(h, w) // 2,
            param1=50,
            param2=30,
            minRadius=min_radius,
            maxRadius=max_radius,
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            cx, cy, r = circles[0][0]
            return int(cx), int(cy), int(r)

        # --- Fallback: Adaptive threshold + contour analysis ---
        # The pupil is typically the darkest, roughly circular region
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # Find the most circular contour in the expected size range
        best = None
        best_circularity = 0

        for cnt in contours:
            area = cv2.contourArea(cnt)
            perimeter = cv2.arcLength(cnt, True)

            if perimeter == 0:
                continue

            circularity = 4 * np.pi * area / (perimeter ** 2)
            radius_est = np.sqrt(area / np.pi)

            if min_radius <= radius_est <= max_radius and circularity > 0.5:
                if circularity > best_circularity:
                    best_circularity = circularity
                    (x, y), radius = cv2.minEnclosingCircle(cnt)
                    best = (int(x), int(y), int(radius))

        return best
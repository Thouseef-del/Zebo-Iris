# backend/services/iris_detection.py

import cv2
import numpy as np
import os
import time
from config import Config


class IrisDetector:
    """Captures an image from the camera and detects the eye region."""

    def __init__(self):
        cascades_dir = os.path.join(os.path.dirname(__file__), "..", "cascades")

        # Use OpenCV's bundled cascades (more reliable than local placeholders)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )

    # --------------------------------------------------
    # Capture iris from camera
    # --------------------------------------------------
    def capture_iris(self):
        """
        Open the camera, capture a frame, detect the eye region.
        Returns (eye_image, message) where eye_image is a grayscale
        cropped eye region or None on failure.
        """
        cap = cv2.VideoCapture(Config.CAMERA_INDEX)

        if not cap.isOpened():
            return None, "Cannot access camera"

        try:
            # Allow camera to warm up
            for _ in range(Config.CAMERA_WARMUP_FRAMES):
                cap.read()

            start = time.time()
            while time.time() - start < Config.CAMERA_CAPTURE_TIMEOUT:
                ret, frame = cap.read()
                if not ret:
                    continue

                eye_image = self._detect_eye(frame)
                if eye_image is not None:
                    return eye_image, "Iris captured successfully"

            return None, "No eye detected within timeout"
        finally:
            cap.release()

    # --------------------------------------------------
    # Capture from an uploaded image (base64 / bytes)
    # --------------------------------------------------
    def detect_from_image(self, image_bytes: bytes):
        """Detect eye region from raw image bytes (e.g. uploaded file)."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return None, "Invalid image data"

        eye_image = self._detect_eye(frame)
        if eye_image is not None:
            return eye_image, "Eye detected from uploaded image"

        return None, "No eye detected in uploaded image"

    # --------------------------------------------------
    # Internal: detect eye from a BGR frame
    # --------------------------------------------------
    def _detect_eye(self, frame):
        """Return the largest detected eye region as a grayscale image."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Detect faces first for better eye localisation
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.3, minNeighbors=5, minSize=(100, 100)
        )

        for (fx, fy, fw, fh) in faces:
            face_roi = gray[fy : fy + fh, fx : fx + fw]
            eyes = self.eye_cascade.detectMultiScale(
                face_roi, scaleFactor=1.1, minNeighbors=10, minSize=(30, 30)
            )

            if len(eyes) > 0:
                # Pick the largest eye region
                eyes = sorted(eyes, key=lambda e: e[2] * e[3], reverse=True)
                ex, ey, ew, eh = eyes[0]
                eye_image = face_roi[ey : ey + eh, ex : ex + ew]
                return eye_image

        # Fallback: try detecting eyes without face detection
        eyes = self.eye_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=10, minSize=(30, 30)
        )

        if len(eyes) > 0:
            eyes = sorted(eyes, key=lambda e: e[2] * e[3], reverse=True)
            ex, ey, ew, eh = eyes[0]
            return gray[ey : ey + eh, ex : ex + ew]

        return None

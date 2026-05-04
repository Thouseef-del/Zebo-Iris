# backend/config.py

import os


class Config:
    """Application configuration."""

    # MongoDB
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "iris_recognition_db")

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "iris-emergency-secret-key")
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1")

    # Auth
    ADMIN_PIN = os.environ.get("ADMIN_PIN", "1234")
    DOCTOR_PIN = os.environ.get("DOCTOR_PIN", "5678")
    JWT_SECRET = os.environ.get("JWT_SECRET", SECRET_KEY)

    # ----- Iris Matching -----
    HAMMING_MATCH_THRESHOLD = float(os.environ.get("HAMMING_MATCH_THRESHOLD", "0.42"))
    DUPLICATE_THRESHOLD = float(os.environ.get("DUPLICATE_THRESHOLD", "0.28"))

    # Rotation compensation: number of cyclic bit-shifts (each ≈ 360°/512 ≈ 0.7°)
    ROTATION_SHIFTS = int(os.environ.get("ROTATION_SHIFTS", "8"))

    # ----- Iris Code Dimensions -----
    # rows × cols of the normalised iris strip / binary iris code
    IRIS_CODE_SIZE = (64, 512)

    # ----- Image Quality Thresholds -----
    QUALITY_BLUR_THRESHOLD = float(os.environ.get("QUALITY_BLUR_THRESHOLD", "20.0"))
    QUALITY_MIN_IRIS_VISIBLE = float(os.environ.get("QUALITY_MIN_IRIS_VISIBLE", "0.20"))
    QUALITY_BRIGHTNESS_LOW = int(os.environ.get("QUALITY_BRIGHTNESS_LOW", "40"))
    QUALITY_BRIGHTNESS_HIGH = int(os.environ.get("QUALITY_BRIGHTNESS_HIGH", "220"))

    # ----- Image Save -----
    IMAGE_SAVE_DIR = os.path.join(os.path.dirname(__file__), "static", "captures")

    # ----- Camera -----
    CAMERA_INDEX = int(os.environ.get("CAMERA_INDEX", "0"))
    CAMERA_WARMUP_FRAMES = 30
    CAMERA_CAPTURE_TIMEOUT = 10  # seconds

# backend/routes/scan.py

from flask import Blueprint, request, jsonify
from services.iris_detection import IrisDetector
from services.iris_segmentation import IrisSegmentation
from services.image_enhancement import ImageEnhancer
from services.iris_code_generator import IrisCodeGenerator
from services.hamming_matcher import HammingMatcher
from services.quality_checker import QualityChecker
from services.image_saver import ImageSaver
from models.user_model import UserModel
from database.db_connection import db

scan_bp = Blueprint("scan", __name__)

# Initialize components
user_model = UserModel(db)
detector = IrisDetector()
segmenter = IrisSegmentation()
enhancer = ImageEnhancer()
code_generator = IrisCodeGenerator()
matcher = HammingMatcher(user_model)
quality_checker = QualityChecker()
image_saver = ImageSaver()


@scan_bp.route("/scan", methods=["GET"])
def scan_iris():
    """
    Scan an iris from the camera and match against the database.

    Returns the matched person's emergency contact details
    along with a confidence score, or 'No Match Found'.
    """
    try:
        # Step 1: Capture iris from camera
        eye_image, message = detector.capture_iris()

        if eye_image is None:
            return jsonify({"status": "Error", "message": message}), 400

        image_saver.save_image(eye_image, prefix="scan_raw")

        # Step 2: Quality check
        quality = quality_checker.assess(eye_image)
        if not quality["passed"]:
            return jsonify({
                "status": "Error",
                "message": "Image quality too low for reliable scanning",
                "quality_issues": quality["issues"],
                "quality_score": quality["score"],
            }), 400

        # Step 3: Segment the iris region
        iris_region = segmenter.segment_iris(eye_image)

        if iris_region is None:
            return jsonify({
                "status": "Error",
                "message": "Iris segmentation failed. Please try again."
            }), 400

        # Step 4: Enhance the image
        enhanced = enhancer.enhance(iris_region)

        if enhanced is None:
            return jsonify({
                "status": "Error",
                "message": "Image enhancement failed."
            }), 400

        image_saver.save_image(enhanced, prefix="scan_enhanced")

        # Step 5: Normalise the iris strip (Daugman rubber-sheet)
        normalised, noise_mask = segmenter.normalize_iris(enhanced)

        if normalised is None:
            return jsonify({
                "status": "Error",
                "message": "Iris normalisation failed."
            }), 400

        # Step 6: Generate binary iris code
        iris_code, expanded_mask = code_generator.generate(normalised, noise_mask)

        if iris_code is None:
            return jsonify({
                "status": "Error",
                "message": "Iris code generation failed."
            }), 400

        # Step 7: Match against database using rotation-compensated Hamming distance
        result = matcher.find_match(iris_code, expanded_mask)
        result["quality_score"] = quality["score"]

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": "Error",
            "message": f"Scan failed: {str(e)}"
        }), 500


@scan_bp.route("/scan/upload", methods=["POST"])
def scan_iris_upload():
    """
    Scan an iris from an uploaded image and match against the database.

    Accepts multipart form data with an 'image' file field.
    """
    if "image" not in request.files:
        return jsonify({"status": "Error", "message": "No image file provided"}), 400

    image_file = request.files["image"]
    image_bytes = image_file.read()

    try:
        # Step 1: Detect eye from uploaded image
        eye_image, message = detector.detect_from_image(image_bytes)

        if eye_image is None:
            return jsonify({"status": "Error", "message": message}), 400

        image_saver.save_image(eye_image, prefix="scan_upload_raw")

        # Step 2: Quality check
        quality = quality_checker.assess(eye_image)
        if not quality["passed"]:
            return jsonify({
                "status": "Error",
                "message": "Image quality too low for reliable scanning",
                "quality_issues": quality["issues"],
                "quality_score": quality["score"],
            }), 400

        # Step 3–6: Same pipeline
        iris_region = segmenter.segment_iris(eye_image)
        if iris_region is None:
            return jsonify({"status": "Error", "message": "Iris segmentation failed."}), 400

        enhanced = enhancer.enhance(iris_region)
        if enhanced is None:
            return jsonify({"status": "Error", "message": "Image enhancement failed."}), 400

        image_saver.save_image(enhanced, prefix="scan_upload_enhanced")

        normalised, noise_mask = segmenter.normalize_iris(enhanced)
        if normalised is None:
            return jsonify({"status": "Error", "message": "Iris normalisation failed."}), 400

        iris_code, expanded_mask = code_generator.generate(normalised, noise_mask)
        if iris_code is None:
            return jsonify({"status": "Error", "message": "Iris code generation failed."}), 400

        # Step 7: Match with rotation compensation + noise masking
        result = matcher.find_match(iris_code, expanded_mask)
        result["quality_score"] = quality["score"]

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": "Error",
            "message": f"Scan failed: {str(e)}"
        }), 500
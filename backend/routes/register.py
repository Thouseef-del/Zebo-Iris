# backend/routes/register.py

from flask import Blueprint, request, jsonify
from services.iris_detection import IrisDetector
from services.iris_segmentation import IrisSegmentation
from services.image_enhancement import ImageEnhancer
from services.iris_code_generator import IrisCodeGenerator
from services.duplicate_checker import DuplicateChecker
from services.quality_checker import QualityChecker
from services.image_saver import ImageSaver
from models.user_model import UserModel
from database.db_connection import db

register_bp = Blueprint("register", __name__)

# Initialize components
user_model = UserModel(db)
detector = IrisDetector()
segmenter = IrisSegmentation()
enhancer = ImageEnhancer()
code_generator = IrisCodeGenerator()
duplicate_checker = DuplicateChecker(user_model)
quality_checker = QualityChecker()
image_saver = ImageSaver()


@register_bp.route("/register", methods=["POST"])
def register_user():
    """
    Register a new user.

    Accepts JSON body with: name, address, phone_no, relationship.
    Captures iris from the camera, processes it, and stores the template.
    """
    data = request.json

    if not data:
        return jsonify({"status": "Error", "message": "No data provided"}), 400

    name = data.get("name")
    address = data.get("address")
    phone_no = data.get("phone_no")
    relationship = data.get("relationship")

    if not all([name, address, phone_no, relationship]):
        return jsonify({
            "status": "Error",
            "message": "All fields are required: name, address, phone_no, relationship"
        }), 400

    try:
        # Step 1: Capture iris from camera
        eye_image, message = detector.capture_iris()

        if eye_image is None:
            return jsonify({"status": "Error", "message": message}), 400

        # Save raw eye capture
        image_saver.save_image(eye_image, prefix="register_raw")

        # Step 2: Quality check
        quality = quality_checker.assess(eye_image)
        if not quality["passed"]:
            return jsonify({
                "status": "Error",
                "message": "Image quality too low for reliable registration",
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

        # Save enhanced iris
        image_saver.save_image(enhanced, prefix="register_enhanced")

        # Step 5: Normalise the iris strip (Daugman rubber-sheet)
        normalised, noise_mask = segmenter.normalize_iris(enhanced)

        if normalised is None:
            return jsonify({
                "status": "Error",
                "message": "Iris normalisation failed."
            }), 400

        # Check iris visibility
        if not quality_checker.check_iris_visibility(noise_mask):
            return jsonify({
                "status": "Error",
                "message": "Too much of the iris is occluded by eyelids. Please open your eye wider."
            }), 400

        # Step 6: Generate binary iris code
        iris_code, expanded_mask = code_generator.generate(normalised, noise_mask)

        if iris_code is None:
            return jsonify({
                "status": "Error",
                "message": "Iris code generation failed."
            }), 400

        # Step 7: Check for duplicate iris
        if duplicate_checker.is_duplicate(iris_code, expanded_mask):
            return jsonify({
                "status": "Error",
                "message": "This iris is already registered in the system."
            }), 409

        # Step 8: Store in MongoDB
        user_id = user_model.create_user(
            name=name,
            address=address,
            phone_no=phone_no,
            relationship=relationship,
            iris_code=iris_code,
            noise_mask=expanded_mask,
        )

        return jsonify({
            "status": "Success",
            "message": "User registered successfully",
            "user_id": user_id,
            "quality_score": quality["score"],
        }), 201

    except Exception as e:
        return jsonify({
            "status": "Error",
            "message": f"Registration failed: {str(e)}"
        }), 500


@register_bp.route("/register/upload", methods=["POST"])
def register_user_upload():
    """
    Register a new user using an uploaded iris image instead of camera.

    Accepts multipart form data with:
      - image: the iris/eye image file
      - name, address, phone_no, relationship as form fields
    """
    name = request.form.get("name")
    address = request.form.get("address")
    phone_no = request.form.get("phone_no")
    relationship = request.form.get("relationship")

    if not all([name, address, phone_no, relationship]):
        return jsonify({
            "status": "Error",
            "message": "All fields are required: name, address, phone_no, relationship"
        }), 400

    if "image" not in request.files:
        return jsonify({"status": "Error", "message": "No image file provided"}), 400

    image_file = request.files["image"]
    image_bytes = image_file.read()

    try:
        # Step 1: Detect eye from uploaded image
        eye_image, message = detector.detect_from_image(image_bytes)

        if eye_image is None:
            return jsonify({"status": "Error", "message": message}), 400

        image_saver.save_image(eye_image, prefix="upload_raw")

        # Step 2: Quality check
        quality = quality_checker.assess(eye_image)
        if not quality["passed"]:
            return jsonify({
                "status": "Error",
                "message": "Image quality too low for reliable registration",
                "quality_issues": quality["issues"],
                "quality_score": quality["score"],
            }), 400

        # Step 3–7: Same pipeline as camera capture
        iris_region = segmenter.segment_iris(eye_image)
        if iris_region is None:
            return jsonify({"status": "Error", "message": "Iris segmentation failed."}), 400

        enhanced = enhancer.enhance(iris_region)
        if enhanced is None:
            return jsonify({"status": "Error", "message": "Image enhancement failed."}), 400

        image_saver.save_image(enhanced, prefix="upload_enhanced")

        normalised, noise_mask = segmenter.normalize_iris(enhanced)
        if normalised is None:
            return jsonify({"status": "Error", "message": "Iris normalisation failed."}), 400

        if not quality_checker.check_iris_visibility(noise_mask):
            return jsonify({
                "status": "Error",
                "message": "Too much of the iris is occluded. Please use a clearer image."
            }), 400

        iris_code, expanded_mask = code_generator.generate(normalised, noise_mask)
        if iris_code is None:
            return jsonify({"status": "Error", "message": "Iris code generation failed."}), 400

        if duplicate_checker.is_duplicate(iris_code, expanded_mask):
            return jsonify({"status": "Error", "message": "This iris is already registered."}), 409

        user_id = user_model.create_user(
            name=name,
            address=address,
            phone_no=phone_no,
            relationship=relationship,
            iris_code=iris_code,
            noise_mask=expanded_mask,
        )

        return jsonify({
            "status": "Success",
            "message": "User registered successfully via upload",
            "user_id": user_id,
            "quality_score": quality["score"],
        }), 201

    except Exception as e:
        return jsonify({
            "status": "Error",
            "message": f"Registration failed: {str(e)}"
        }), 500
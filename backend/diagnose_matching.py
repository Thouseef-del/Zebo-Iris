# backend/diagnose_matching.py
"""
Diagnose iris matching — Compute iris codes from two images of the same
person and report the Hamming distance to understand why matching fails.
"""

import os, sys, cv2, numpy as np

# Make sure imports work
sys.path.insert(0, os.path.dirname(__file__))

from services.iris_detection import IrisDetector
from services.iris_segmentation import IrisSegmentation
from services.image_enhancement import ImageEnhancer
from services.iris_code_generator import IrisCodeGenerator
from services.hamming_matcher import HammingMatcher

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_data")

detector = IrisDetector()
segmenter = IrisSegmentation()
enhancer = ImageEnhancer()
code_gen = IrisCodeGenerator()


def process_image(image_path):
    """Run the full pipeline on an image, return (iris_code, mask, debug_info)."""
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    info = {"file": os.path.basename(image_path)}

    # Step 1: Detect eye
    eye_image, msg = detector.detect_from_image(image_bytes)
    if eye_image is None:
        info["error"] = f"Eye detection failed: {msg}"
        return None, None, info

    info["eye_shape"] = eye_image.shape
    info["eye_mean_brightness"] = float(np.mean(eye_image))

    # Step 2: Segment iris
    iris_region = segmenter.segment_iris(eye_image)
    if iris_region is None:
        info["error"] = "Iris segmentation failed"
        return None, None, info

    info["iris_shape"] = iris_region.shape

    # Step 3: Enhance
    enhanced = enhancer.enhance(iris_region)
    if enhanced is None:
        info["error"] = "Enhancement failed"
        return None, None, info

    # Step 4: Normalize
    result = segmenter.normalize_iris(enhanced)
    if isinstance(result, tuple):
        normalised, noise_mask = result
    else:
        normalised = result
        noise_mask = None

    if normalised is None:
        info["error"] = "Normalisation failed"
        return None, None, info

    info["normalised_shape"] = normalised.shape
    if noise_mask is not None:
        info["mask_visible_pct"] = round(float(np.mean(noise_mask)) * 100, 1)

    # Step 5: Generate iris code
    result = code_gen.generate(normalised, noise_mask)
    if isinstance(result, tuple):
        iris_code, expanded_mask = result
    else:
        iris_code = result
        expanded_mask = None

    if iris_code is None:
        info["error"] = "Code generation failed"
        return None, None, info

    info["code_length"] = len(iris_code)
    info["code_ones_pct"] = round(sum(iris_code) / len(iris_code) * 100, 1)

    return iris_code, expanded_mask, info


def main():
    images = sorted(os.listdir(SAMPLE_DIR))
    images = [f for f in images if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    print(f"\nFound {len(images)} images in sample_data/\n")

    # Process all images
    codes = []
    for img_name in images:
        path = os.path.join(SAMPLE_DIR, img_name)
        code, mask, info = process_image(path)

        status = "OK" if code else f"FAIL: {info.get('error', '?')}"
        print(f"  {img_name[:40]:<42} {status}")
        if code:
            for k, v in info.items():
                if k != "file":
                    print(f"      {k}: {v}")
        codes.append((img_name, code, mask, info))
        print()

    # Compute pairwise Hamming distances
    valid = [(n, c, m) for n, c, m, i in codes if c is not None]

    if len(valid) < 2:
        print("Not enough valid codes to compare.")
        return

    print(f"\n{'='*70}")
    print("  PAIRWISE HAMMING DISTANCES")
    print(f"{'='*70}")

    # Create a simple matcher just for the static method
    for i in range(len(valid)):
        for j in range(i + 1, len(valid)):
            name_a, code_a, mask_a = valid[i]
            name_b, code_b, mask_b = valid[j]

            # Simple Hamming (no rotation)
            hd_simple = HammingMatcher.hamming_distance(code_a, code_b, mask_a, mask_b)

            short_a = name_a[:25]
            short_b = name_b[:25]

            match_symbol = "MATCH" if hd_simple < 0.35 else ("CLOSE" if hd_simple < 0.40 else "NO")
            print(f"  {short_a} vs {short_b}  HD={hd_simple:.4f}  [{match_symbol}]")

    print(f"\n  Threshold: 0.35 (MATCH if HD < 0.35)")
    print(f"  Random iris pairs typically have HD ≈ 0.50")
    print(f"  Same iris pairs should have HD < 0.35")


if __name__ == "__main__":
    main()

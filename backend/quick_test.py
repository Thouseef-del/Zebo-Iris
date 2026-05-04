# backend/quick_test.py
"""Quick test: process two images of the same person, check if they match."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from services.iris_detection import IrisDetector
from services.iris_segmentation import IrisSegmentation
from services.image_enhancement import ImageEnhancer
from services.iris_code_generator import IrisCodeGenerator
from services.hamming_matcher import HammingMatcher
import numpy as np

detector = IrisDetector()
segmenter = IrisSegmentation()
enhancer = ImageEnhancer()
code_gen = IrisCodeGenerator()

SAMPLE = os.path.join(os.path.dirname(__file__), "sample_data")

def process(name):
    with open(os.path.join(SAMPLE, name), "rb") as f:
        data = f.read()
    eye, _ = detector.detect_from_image(data)
    if eye is None:
        return None, None, "eye detection failed"
    iris = segmenter.segment_iris(eye)
    if iris is None:
        return None, None, "segmentation failed"
    enh = enhancer.enhance(iris)
    result = segmenter.normalize_iris(enh)
    if isinstance(result, tuple):
        norm, mask = result
    else:
        norm, mask = result, None
    if norm is None:
        return None, None, "normalisation failed"
    vis = round(float(np.mean(mask)) * 100, 1) if mask is not None else -1
    result2 = code_gen.generate(norm, mask)
    if isinstance(result2, tuple):
        code, emask = result2
    else:
        code, emask = result2, None
    return code, emask, vis

images = sorted([f for f in os.listdir(SAMPLE) if f.lower().endswith(('.jpg', '.jpeg'))])

# Process first two images
print("Processing images...")
codes = []
for img in images[:4]:
    code, mask, vis = process(img)
    status = "OK" if code else vis
    vis_str = f"{vis}%" if isinstance(vis, float) else vis
    print(f"  {img[:45]}: {status} (visibility: {vis_str})")
    if code:
        codes.append((img, code, mask))

print(f"\nPairwise Hamming distances (threshold=0.42):")
for i in range(len(codes)):
    for j in range(i+1, len(codes)):
        n1, c1, m1 = codes[i]
        n2, c2, m2 = codes[j]
        hd = HammingMatcher.hamming_distance(c1, c2, m1, m2)
        match = "YES" if hd < 0.42 else "NO"
        print(f"  {n1[:25]} vs {n2[:25]}: HD={hd:.4f} Match={match}")

#!/usr/bin/env python3

INPUT_DIR = "060-rotate-crop-level"
OUTPUT_DIR = "065-remove-page-borders"

# === Tuning parameters ===
BORDER_SIZE = 10  # pixels

"""
AI prompt:

create a python script to remove grey (or black) page borders from scanned images.
the pages are white with black text.
the pages are no perfect rectangles, rather crooked trapezes with crooked lines...
so the algorithm should "overcut" the pages:
it should cut at the inner-most page edge,
so where the page edge is further outside some white area from the page is removed.

the script should process an input directory with *.tiff images
and write output images to an output directory (same image format).
the input and output paths should be hard-coded in the script,
so the script takes no command-line arguments.
the script should be based on the PIL (pillow) image library
(and on the opencv and numpy libraries when necessary)

...
"""

import os
from PIL import Image
import numpy as np
import cv2

def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    rect[0] = pts[np.argmin(s)]  # top-left
    rect[2] = pts[np.argmax(s)]  # bottom-right
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left
    return rect

def process_image(in_path, out_path):
    img = cv2.imread(in_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Threshold to isolate white page
    _, mask = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8))
    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    page_contour = max(contours, key=cv2.contourArea)
    # Approximate contour to a quadrilateral
    epsilon = 0.02 * cv2.arcLength(page_contour, True)
    approx = cv2.approxPolyDP(page_contour, epsilon, True)
    if len(approx) != 4:
        print("Warning: contour approximation did not yield 4 points. Using convex hull instead.")
        approx = cv2.convexHull(page_contour)
        # Optionally select 4 corners from convex hull manually
    # Extract the 4 corner points
    pts = approx.reshape(4, 2)
    # Order the points consistently
    rect = order_points(pts)
    # Compute perspective transform
    # Compute width and height of new rectangle
    widthA = np.linalg.norm(rect[2] - rect[3])
    widthB = np.linalg.norm(rect[1] - rect[0])
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.linalg.norm(rect[1] - rect[2])
    heightB = np.linalg.norm(rect[0] - rect[3])
    maxHeight = max(int(heightA), int(heightB))
    # Destination points for the "straight" rectangle
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")
    # Perspective transform
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
    # Add internal white border
    # to remove grey artifacts from cropping crooked page edges
    # Create a white canvas of the same size
    h, w = warped.shape[:2]
    canvas = np.ones_like(warped) * 255  # white
    # Copy the warped content inside the canvas, leaving a white border
    b = BORDER_SIZE
    canvas[b:h-b, b:w-b] = warped[b:h-b, b:w-b]
    out_image = canvas
    # Save the result
    print(f"writing {out_path}")
    cv2.imwrite(out_path, out_image)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    files = [f for f in sorted(os.listdir(INPUT_DIR)) if f.lower().endswith((".tif", ".tiff"))]
    if not files:
        print("No TIFF files found in", INPUT_DIR)
        return
    for f in files:
        in_path = os.path.join(INPUT_DIR, f)
        out_path = os.path.join(OUTPUT_DIR, f)
        if os.path.exists(out_path): continue
        try:
            process_image(in_path, out_path)
        except Exception as e:
            print(f"Error processing {f}: {e}")

if __name__ == "__main__":
    main()

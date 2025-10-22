#!/usr/bin/env python3

# benchmarks:
# imagemagick version: 191...196 seconds for 941 MB of 304 tiff files
# PIL version: 24 seconds for 941 MB of 304 tiff files -> 8x faster
# parallel PIL version: 7 seconds for 941 MB of 304 tiff files on an 8 core CPU -> 4x faster

import os
import sys
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from PIL import Image, ImageStat

src = "065-remove-page-borders"
dst = os.path.splitext(os.path.basename(__file__))[0]
max_workers = os.cpu_count() or 4  # use all available cores

out_path = f"{dst}.txt"
if os.path.exists(out_path):
    print(f"error: out_path exists: {out_path}")
    sys.exit(1)

os.makedirs(dst, exist_ok=True)


def compute_lightness(filepath):
    """Compute mean lightness (0–100) of a TIFF image."""
    filename = os.path.basename(filepath)
    page_number = filename[:-5].lstrip("0") or "0"
    page_number = int(page_number)

    # if not page_number in [1, 8, 260]: return (0.0, page_number) # debug

    try:
        with Image.open(filepath) as img:
            gray = img.convert("L")
            stat = ImageStat.Stat(gray)
            lightness = stat.mean[0] / 255 * 100
    except Exception:
        lightness = -1.0
    return (lightness, page_number)


def main():
    t1 = int(time.time())

    # Collect all TIFF files
    tiff_files = sorted(
        os.path.join(src, f) for f in os.listdir(src) if f.lower().endswith(".tiff")
    )

    results = []

    # Process in parallel
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(compute_lightness, f): f for f in tiff_files}
        for i, future in enumerate(as_completed(futures), start=1):
            lightness, page_number = future.result()
            print(f"{lightness:08.4f} {page_number}")
            results.append((lightness, page_number))

    # Sort: lightness descending, page_number ascending
    results.sort(key=lambda x: (-x[0], x[1]))

    # Write results
    print(f"writing {out_path}")
    with open(out_path, "w", encoding="utf-8") as f:
        for lightness, page_number in results:
            f.write(f"{lightness:010.6f} {page_number}\n")

    t2 = int(time.time())
    print(f"done {len(results)} pages in {t2 - t1} seconds using {max_workers} cores")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Debug posterization output."""

from pathlib import Path
import numpy as np
from PIL import Image
from skimage import color as skcolor

def posterize_aggressive(rgb: np.ndarray, max_colors: int = 8) -> np.ndarray:
    """Flatten to max_colors via k-means in Lab space."""
    h, w = rgb.shape[:2]
    lab = skcolor.rgb2lab(rgb.astype(np.float32) / 255.0)
    lab_flat = lab.reshape(-1, 3)

    # K-means
    rng = np.random.default_rng(42)
    idx = rng.choice(len(lab_flat), max_colors, replace=False)
    centers = lab_flat[idx].copy()

    for _ in range(10):
        dists = np.linalg.norm(lab_flat[:, None] - centers[None], axis=2)
        labels = dists.argmin(axis=1)
        for i in range(max_colors):
            if (labels == i).any():
                centers[i] = lab_flat[labels == i].mean(axis=0)

    # Map back
    dists = np.linalg.norm(lab_flat[:, None] - centers[None], axis=2)
    labels = dists.argmin(axis=1)
    lab_flat[...] = centers[labels]
    lab = lab_flat.reshape(h, w, 3)

    rgb_out = skcolor.lab2rgb(lab)
    return (np.clip(rgb_out, 0, 1) * 255).astype(np.uint8)


# Load image
img_path = "input_images/order_0002_img_0331.png"
rgb = np.array(Image.open(img_path).convert("RGB"), dtype=np.uint8)

print(f"Original shape: {rgb.shape}")
print(f"Original unique colors: {len(np.unique(rgb.reshape(-1, 3), axis=0))}")

# Posterize
rgb_poster = posterize_aggressive(rgb, max_colors=8)

print(f"Posterized shape: {rgb_poster.shape}")
print(f"Posterized unique colors: {len(np.unique(rgb_poster.reshape(-1, 3), axis=0))}")

# Save for visual inspection
Image.fromarray(rgb_poster).save("debug_posterized_output.png")
print("Saved: debug_posterized_output.png")

# Check what gets extracted as binary
gray = rgb_poster.mean(axis=2).astype(np.uint8)
binary = gray > 127
print(f"Binary threshold > 127: {binary.sum()} pixels out of {binary.size}")

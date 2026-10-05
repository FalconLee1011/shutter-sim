"""File IO handler"""

import os

import cv2
import numpy as np


def save_image(
    output_root: str, filename: str, input_img: cv2.Mat, raw: bool = False
) -> None:
    """Saves image to tiff or raw npy."""
    os.makedirs(output_root, exist_ok=True)
    output_path = os.path.join(output_root, filename)
    if raw:
        np.save(f"{output_path}.npy", input_img)
    else:
        cv2.imwrite(
            f"{output_path}.tiff", input_img, [cv2.IMWRITE_TIFF_COMPRESSION, 1]
        )

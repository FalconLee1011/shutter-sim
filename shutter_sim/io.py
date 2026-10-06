"""File IO handler"""

import os

import cv2
import numpy as np

DISPLAY_GAMMA = 1 / 2.2

def to_display_u8(
    input_img: np.ndarray, gamma: float = DISPLAY_GAMMA
) -> np.ndarray:
    linear = np.clip(np.asarray(input_img, dtype=np.float32), 0.0, 1.0)
    encoded = np.power(linear, gamma)
    return np.rint(encoded * 255.0).astype(np.uint8)

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

    cv2.imwrite(f"{output_path}.png", to_display_u8(input_img))

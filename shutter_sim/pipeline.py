"""The main pipeline"""

import math
import random

import cv2
import numpy as np

from .constants import (BAYER_DXY, BLACK_LEVEL_OFFSET, CCM, LSC_K,
                        SENSOR_DEFECT_RATE, TONE_MAGIC_NUMBER, WB_GAINS)


def to_bayer_plane(input_img: cv2.Mat) -> np.ndarray:
    """One sample per pixel. GBRG, OpenCV BGR channel order."""
    height, width, _ = input_img.shape
    raw_bayer = np.zeros((height, width), np.float32)

    step = 2
    for rx in range(0, width, step):
        for ry in range(0, height, step):
            for d in BAYER_DXY:
                dy, dx, ch = d
                x = rx + dx
                y = ry + dy
                if x < width and y < height:
                    raw_bayer[y][x] = input_img[y][x][ch]

    return raw_bayer


def get_cfa_layers(input_img: cv2.Mat) -> list[cv2.Mat]:
    """Separates R, G, B layers to reflect CFA effect"""
    height, width, _ = input_img.shape
    cfa_layers = [
        np.zeros((height, width, 3), np.float32),  # B
        np.zeros((height, width, 3), np.float32),  # G
        np.zeros((height, width, 3), np.float32),  # R
    ]

    step = 2
    for rx in range(0, width, step):
        for ry in range(0, height, step):
            for d in BAYER_DXY:
                dy, dx, ch = d
                x = rx + dx
                y = ry + dy
                if x < width and y < height:
                    cfa_layers[ch][y][x][ch] = input_img[y][x][ch]

    return cfa_layers


def reverse_black_level_correction(
    input_img: cv2.Mat
) -> cv2.Mat:
    """Reverse Black Level Correction"""
    height, width, _ = input_img.shape
    img = input_img.copy()
    step = 2
    for rx in range(0, width, step):
        for ry in range(0, height, step):
            for d in BAYER_DXY:
                dy, dx, ch = d
                x = rx + dx
                y = ry + dy
                if x < width and y < height:
                    img[y, x, ch] = (
                        BLACK_LEVEL_OFFSET
                        + (1 - BLACK_LEVEL_OFFSET) * img[y][x][ch]
                    )

    return img


def reverse_dead_pixel(input_img: cv2.Mat) -> cv2.Mat:
    """Generates random dead pixel."""
    height, width, _ = input_img.shape
    img = input_img.copy()
    defect_count = math.ceil(height * width * SENSOR_DEFECT_RATE)
    positions = random.sample(range(width * height), defect_count)

    defect_pixels = [
        (position % width, position // width) for position in positions
    ]

    for x, y in defect_pixels:
        img[y][x] = np.zeros(3)

    return img


def reverse_lsc(input_img: cv2.Mat) -> cv2.Mat:
    """Reverts Lens Shading Correction."""
    height, width, _ = input_img.shape
    img = input_img.copy()
    center_x = (width - 1) / 2
    center_y = (height - 1) / 2
    for x in range(0, width):
        for y in range(0, height):
            dist_x = (x - center_x) / center_x
            dist_y = (y - center_y) / center_y
            d = dist_x**2 + dist_y**2
            shading = 1 / (1 + LSC_K * d)
            img[y][x] *= shading

    return img


def reverse_white_balance(input_img: cv2.Mat) -> cv2.Mat:
    """Reverse White Balance"""
    height, width, _ = input_img.shape
    img = input_img.copy()
    for x in range(0, width):
        for y in range(0, height):
            img[y][x][0] = input_img[y][x][0] / WB_GAINS["B"]
            img[y][x][1] = input_img[y][x][1] / WB_GAINS["G"]
            img[y][x][2] = input_img[y][x][2] / WB_GAINS["R"]

    return img


def recreate_bayer(input_img: cv2.Mat) -> list[cv2.Mat]:
    """Generate bayer from RGB aka 'remosaicing'."""
    img = input_img.copy()
    height, width, _ = input_img.shape
    step = 2

    bayer = np.zeros((height, width, 3), np.float32)

    for rx in range(0, width, step):
        for ry in range(0, height, step):
            for d in BAYER_DXY:
                dy, dx, ch = d
                x = rx + dx
                y = ry + dy
                if x < width and y < height:
                    bayer[y][x][ch] = img[y][x][ch]

    return bayer


def reverse_ccm(input_img: cv2.Mat) -> cv2.Mat:
    """Reverse Color Correction Matrix"""
    matrix = np.asarray(CCM, dtype=np.float32)
    inverse = np.linalg.inv(matrix[::-1, ::-1])
    height, width, _ = input_img.shape
    img = input_img.copy()
    for x in range(0, width):
        for y in range(0, height):
            rb = input_img[y][x][0]
            rg = input_img[y][x][1]
            rr = input_img[y][x][2]
            img[y][x][0] = (
                rb * inverse[0][0] + rg * inverse[0][1] + rr * inverse[0][2]
            )
            img[y][x][1] = (
                rb * inverse[1][0] + rg * inverse[1][1] + rr * inverse[1][2]
            )
            img[y][x][2] = (
                rb * inverse[2][0] + rg * inverse[2][1] + rr * inverse[2][2]
            )

    return img


def reverse_tone_mapping(input_img: cv2.Mat) -> cv2.Mat:
    """Reverse Tone Mapping"""
    height, width, _ = input_img.shape
    img = np.zeros((height, width, 3), np.float32)
    for x in range(0, width):
        for y in range(0, height):
            img[y][x][0] = (input_img[y][x][0] / 255) ** TONE_MAGIC_NUMBER
            img[y][x][1] = (input_img[y][x][1] / 255) ** TONE_MAGIC_NUMBER
            img[y][x][2] = (input_img[y][x][2] / 255) ** TONE_MAGIC_NUMBER

    return img

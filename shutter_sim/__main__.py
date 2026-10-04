"""Shutter Sim, reversed ISP pipeline simulator
"""

import os
import argparse

import cv2
import numpy as np

from .pipeline import (reverse_tone_mapping, reverse_ccm, recreate_bayer,
                       reverse_white_balance, reverse_lsc, reverse_dead_pixel,
                       reverse_black_level_correction, get_cfa_layers)

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--input_file")


def run_pipeline(raw_img: cv2.Mat):
    """Run the main pipeline"""
    before_tm = reverse_tone_mapping(raw_img)
    # cv2.imshow("before_tm", before_tm)

    before_ccm = reverse_ccm(before_tm)
    # cv2.imshow("before_ccm", before_ccm)

    bayer = recreate_bayer(before_ccm)
    # cv2.imshow("Bayer", bayer_layers[3])

    before_wb = reverse_white_balance(bayer)
    # cv2.imshow("before_wb", before_wb)

    before_lsc = reverse_lsc(before_wb)
    # cv2.imshow("before_lsc", before_lsc)

    before_dpc = reverse_dead_pixel(before_lsc)
    # cv2.imshow("before_dpc", before_dpc)

    before_blc = reverse_black_level_correction(before_dpc)
    # cv2.imshow("before_blc", before_blc)

    cfa_layers = get_cfa_layers(before_blc)

    pipeline = np.hstack(
        tuple(reversed([before_tm, before_ccm, bayer,
              before_wb, before_lsc, before_dpc, before_blc]))
    )

    cv2.imshow("pipeline", pipeline)
    cv2.imshow("cfa_layers", np.hstack(cfa_layers))

    cv2.waitKey(0)
    cv2.destroyAllWindows()


def main():
    """Main"""
    args = parser.parse_args()
    if not args.input_file or not os.path.exists(args.input_file):
        print("File does not exist, exiting.")
        return

    raw_img = cv2.imread(args.input_file)

    cv2.imshow("original", raw_img)
    run_pipeline(raw_img.copy())


if __name__ == "__main__":
    main()

"""Shutter Sim, reversed ISP pipeline simulator"""

import argparse
import os
from pathlib import Path
from typing import Literal

import cv2
import numpy as np

from .constants import DEFAULT_OUTPUT_ROOT
from .io import save_image
from .pipeline import (get_cfa_layers, recreate_bayer,
                       reverse_black_level_correction, reverse_ccm,
                       reverse_dead_pixel, reverse_lsc, reverse_tone_mapping,
                       reverse_white_balance, to_bayer_plane)

parser = argparse.ArgumentParser()

parser.add_argument("-i", "--input_file")
parser.add_argument("-o", "--output", action="store_true")
parser.add_argument("-p", "--preview", action="store_true")
parser.add_argument("--output_root")
parser.add_argument("--output_format")


def run_pipeline(
    raw_img: cv2.Mat,
    preview: bool,
    output: bool,
    output_root: str,
    raw_filename: str,
    output_format: Literal["tiff", "raw"],
):
    """Run the main pipeline"""
    before_tm = reverse_tone_mapping(raw_img)
    before_ccm = reverse_ccm(before_tm)
    bayer = recreate_bayer(before_ccm)
    before_wb = reverse_white_balance(bayer)
    before_lsc = reverse_lsc(before_wb)
    before_dpc = reverse_dead_pixel(before_lsc)
    before_blc = reverse_black_level_correction(before_dpc)
    cfa_layers = get_cfa_layers(before_blc)
    raw_bayer = to_bayer_plane(before_blc)

    if preview:
        pipeline = np.hstack(
            tuple(
                reversed(
                    [
                        before_tm,
                        before_ccm,
                        bayer,
                        before_wb,
                        before_lsc,
                        before_dpc,
                        before_blc,
                    ]
                )
            )
        )

        cv2.imshow("original", raw_img)
        cv2.imshow("Full Pipeline", pipeline)
        cv2.imshow("CFA Layers", np.hstack(cfa_layers))
        cv2.imshow("Bayer", raw_bayer)

        cv2.waitKey(0)
        cv2.destroyAllWindows()

    if output:
        _output_root = os.path.join(output_root, Path(raw_filename).stem)
        store_raw = output_format.lower() == "raw"
        save_image(_output_root, "1_before_tm", before_tm, store_raw)
        save_image(_output_root, "2_before_ccm", before_ccm, store_raw)
        save_image(_output_root, "3_bayer", bayer, store_raw)
        save_image(_output_root, "4_before_wb", before_wb, store_raw)
        save_image(_output_root, "5_before_lsc", before_lsc, store_raw)
        save_image(_output_root, "6_before_dpc", before_dpc, store_raw)
        save_image(_output_root, "7_before_blc", before_blc, store_raw)
        save_image(_output_root, "8_cfa_b", cfa_layers[0], store_raw)
        save_image(_output_root, "8_cfa_g", cfa_layers[1], store_raw)
        save_image(_output_root, "8_cfa_r", cfa_layers[2], store_raw)
        save_image(_output_root, "9_raw_bayer", raw_bayer, store_raw)


def main():
    """Main"""
    args = parser.parse_args()
    show_preview = args.preview
    outputs = args.output
    if not args.input_file or not os.path.exists(args.input_file):
        print("File does not exist, exiting.")
        return

    if not show_preview and not outputs:
        print(
            "No action specified, please specify at least one action via flag --preview or --output"
        )

    raw_img = cv2.imread(args.input_file)

    run_pipeline(
        raw_img.copy(),
        show_preview,
        outputs,
        args.output_root or DEFAULT_OUTPUT_ROOT,
        args.input_file,
        args.output_format,
    )


if __name__ == "__main__":
    main()

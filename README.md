# Shutter Sim

Shutter Sim is an educational image signal processor (ISP) simulator. Starting with a JPEG, it works backward through a simplified camera pipeline to visualize synthetic Bayer samples and the effects of color correction, white balance, lens shading, defective pixels, and black level.

Please note that this simulation uses parameters that simply spawned on my head rather than measured camera calibration. **It creates a demonstration, not recover the original camera's RAW data.**

## Usage
Install the virtual environment first.
```bash
pipenv install
```

Run main.py
```bash
$ pipenv run python main.py -h
usage: main.py [-h] [-i INPUT_FILE]

options:
  -h, --help            show this help message and exit
  -i, --input_file INPUT_FILE
```

The program opens three OpenCV windows:

- **original** — the decoded input image.
- **pipeline** — seven intermediate images, displayed from the synthetic sensor stage on the left toward the processed image on the right.
- **cfa_layers** — the final Bayer samples separated into blue, green, and red views, from left to right.

You will see something like this:
![](./docs/result_preview.jpg)

Press any key to quit.

## Pipeline

The diagram shows the **ISP pipeline**, from sensor data to JPEG:

![Forward ISP pipeline: black-level correction, defective-pixel correction, lens-shading correction, white balance, demosaicing, color correction, and tone mapping leading to JPEG.](./docs/PipelineDiagram.jpg)

The simulator follows the opposite direction:

| Reverse stage              | Simulation                                                                                      |
| -------------------------- | ----------------------------------------------------------------------------------------------- |
| Tone Mapping               | Normalize the input to 0–1 and raise each channel to 2.2, approximating inverse gamma encoding. |
| Color Correction Matrix    | Apply the inverse of the configured forward CCM to linear color values.                         |
| Demosaicing                | "**Remosaic**" the image by retaining one channel per pixel in a GBRG pattern.                  |
| White Balance              | Divide Bayer samples by the configured channel gains.                                           |
| Lens-shading Correction    | Apply smooth spatial darkening toward the edges and corners.                                    |
| Defective-Pixel Correction | Inject random dead pixels.                                                                      |
| Black-Level Correction     | Restore a normalized black offset to each sampled Bayer channel.                                |

Remosaicing and defect injection simulate earlier stages; they are not exact inverses of demosaicing or defect correction. The gamma approximation also does not undo an unknown camera's complete tone mapping.

## Simulation Settings

Feel free to edit the magic constants at the top of [main.py](./main.py) feel different results:

| Setting              | Default                      | Meaning                                                          |
| -------------------- | ---------------------------- | ---------------------------------------------------------------- |
| `SENSOR_BITS`        | `12`                         | Assumed sensor bit depth used to normalize the black level.      |
| `BLACK_LEVELS`       | `512`                        | Assumed black level in sensor code values.                       |
| `SENSOR_DEFECT_RATE` | `0.00097`                    | Fraction used to calculate the requested defect count.           |
| `LSC_K`              | `1.25`                       | Lens-shading strength; larger values darken the edges more.      |
| `WB_GAINS`           | R: `1.0`, G: `1.2`, B: `2.0` | Forward white-balance gains; reverse processing divides by them. |
| `TONE_MAGIC_NUMBER`  | `2.2`                        | Exponent used for approximate inverse gamma encoding.            |
| `CCM`                | Illustrative 3×3 matrix      | Forward color transform, defined in RGB order.                   |
| `BAYER_DXY`          | GBRG                         | Bayer sample positions and their OpenCV BGR channel indices.     |


## Notes

- The pipeline stores image in **float32** for easier development.
- Bayer previews use three-channel arrays with two missing channels set to zero at each pixel. Actual Bayer data normally stores one sample per pixel.
- `SENSOR_BITS` does not quantize the output to specified bits.
- Linear values are displayed directly, so intermediate images appear darker than a display-encoded image.

"""Stores constants for the pipeline"""

SENSOR_BITS = 12
SENSOR_DEFECT_RATE = 0.00097
BLACK_LEVELS = 512
BLACK_LEVEL_OFFSET = BLACK_LEVELS / ((2 ** SENSOR_BITS) - 1)

LSC_K = 1.25
WB_GAINS = {"R": 1.0, "G": 1.2, "B": 2.0}
TONE_MAGIC_NUMBER = 2.2
CCM = [
    [1.2, -0.1, -0.1],
    [-0.1, 1.2, -0.1],
    [-0.1, -0.1, 1.2],
]
BAYER_DXY = [
    [0, 0, 1],
    [0, 1, 0],
    [1, 0, 2],
    [1, 1, 1],
]

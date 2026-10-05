import numpy as np
import cv2
import pytest

from shutter_sim.io import save_image


@pytest.fixture
def linear_bgr():
    """Float image with a negative and a value above 1, both legal after inverse CCM."""
    return np.array(
        [[[-0.25, 0.0, 0.5], [1.0, 1.5, 0.125]]],
        dtype=np.float32,
    )


@pytest.fixture
def bayer_plane():
    return np.array([[0.0, 0.4], [0.8, 0.2]], dtype=np.float32)


def test_tiff_round_trip_keeps_float_shape_and_values(tmp_path, linear_bgr):
    save_image(str(tmp_path), "stage", linear_bgr, raw=False)

    path = tmp_path / "stage.tiff"
    assert path.is_file()
    assert not (tmp_path / "stage.npy").exists()

    loaded = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    assert loaded.dtype == np.float32
    assert loaded.shape == linear_bgr.shape
    np.testing.assert_allclose(loaded, linear_bgr, atol=1e-6)


def test_npy_round_trip_keeps_bayer_plane(tmp_path, bayer_plane):
    save_image(str(tmp_path), "9_raw_bayer", bayer_plane, raw=True)

    path = tmp_path / "9_raw_bayer.npy"
    assert path.is_file()
    assert not (tmp_path / "9_raw_bayer.tiff").exists()

    loaded = np.load(path)
    assert loaded.dtype == np.float32
    assert loaded.shape == bayer_plane.shape
    np.testing.assert_array_equal(loaded, bayer_plane)


def test_save_image_creates_missing_directory(tmp_path, linear_bgr):
    root = tmp_path / "outputs" / "IMG_0889"
    save_image(str(root), "1_before_tm", linear_bgr, raw=False)
    assert (root / "1_before_tm.tiff").is_file()

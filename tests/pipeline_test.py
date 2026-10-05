"""Numeric contracts for the reverse ISP blocks; no GUI or image files needed."""

import random

import numpy as np
import pytest

from shutter_sim import pipeline as p


@pytest.fixture
def color_image():
    """Distinct, nonzero channel values make channel swaps easy to detect."""
    return np.broadcast_to(
        np.array([0.2, 0.4, 0.8], np.float32), (3, 5, 3)
    ).copy()


@pytest.fixture
def gbrg_channels():
    return np.array([[1, 0, 1, 0, 1], [2, 1, 2, 1, 2], [1, 0, 1, 0, 1]])


def test_remosaic_selects_gbrg_channels(color_image, gbrg_channels):
    result = p.recreate_bayer(color_image)
    mask = np.eye(3, dtype=bool)[gbrg_channels]
    np.testing.assert_array_equal(result[mask], color_image[mask])
    assert np.all(result[~mask] == 0)
    assert result.shape == color_image.shape
    assert result.dtype == np.float32


def test_bayer_plane_selects_one_sample_per_pixel(color_image, gbrg_channels):
    expected = np.array([0.2, 0.4, 0.8], np.float32)[gbrg_channels]
    result = p.to_bayer_plane(color_image)
    np.testing.assert_array_equal(result, expected)
    assert result.shape == (3, 5)
    assert result.dtype == np.float32


def test_cfa_layers_separate_blue_green_red(color_image, gbrg_channels):
    layers = p.get_cfa_layers(color_image)
    assert len(layers) == 3
    for channel, layer in enumerate(layers):
        expected = np.zeros_like(color_image)
        expected[..., channel][gbrg_channels == channel] = color_image[
            0, 0, channel
        ]
        np.testing.assert_array_equal(layer, expected)
        assert layer.dtype == np.float32
    np.testing.assert_array_equal(sum(layers), p.recreate_bayer(color_image))


@pytest.mark.parametrize("shape", [(1, 1), (1, 5), (5, 1), (4, 6)])
def test_bayer_helpers_cover_small_and_even_images(shape):
    source = np.ones((*shape, 3), np.float32)
    mosaic = p.recreate_bayer(source)
    np.testing.assert_array_equal(mosaic.sum(axis=2), np.ones(shape))
    np.testing.assert_array_equal(p.to_bayer_plane(source), np.ones(shape))
    np.testing.assert_array_equal(sum(p.get_cfa_layers(source)), mosaic)


@pytest.mark.parametrize(
    "signal, expected", [(0.0, 0.125), (0.5, 0.5625), (1.0, 1.0)]
)
def test_black_level_only_updates_sampled_channels(
    monkeypatch, gbrg_channels, signal, expected
):
    monkeypatch.setattr(p, "BLACK_LEVEL_OFFSET", 0.125)
    mask = np.eye(3, dtype=bool)[gbrg_channels]
    source = np.zeros((3, 5, 3), np.float32)
    source[mask] = signal
    result = p.reverse_black_level_correction(source)
    np.testing.assert_allclose(result[mask], expected)
    assert np.all(result[~mask] == 0)
    np.testing.assert_allclose((result[mask] - 0.125) / 0.875, signal)


def test_dead_pixels_use_flat_positions_correctly(monkeypatch):
    source = np.ones((3, 5, 3), np.float32)
    monkeypatch.setattr(p, "SENSOR_DEFECT_RATE", 0.2)

    def sample(population, count):
        assert list(population) == list(range(15))
        assert count == 3
        return [0, 7, 14]

    monkeypatch.setattr(p.random, "sample", sample)
    expected = source.copy()
    expected[0, 0] = expected[1, 2] = expected[2, 4] = 0
    np.testing.assert_array_equal(p.reverse_dead_pixel(source), expected)


@pytest.mark.parametrize("rate, count", [(0, 0), (0.01, 1), (0.21, 4), (1, 15)])
def test_dead_pixel_count_and_uniqueness(monkeypatch, rate, count):
    monkeypatch.setattr(p, "SENSOR_DEFECT_RATE", rate)
    monkeypatch.setattr(p.random, "sample", random.Random(42).sample)
    result = p.reverse_dead_pixel(np.ones((3, 5, 3), np.float32))
    assert np.count_nonzero(np.all(result == 0, axis=2)) == count
    assert np.all((result == 0) | (result == 1))


@pytest.mark.parametrize("shape", [(5, 7), (4, 6)])
def test_lsc_is_symmetric_and_preserves_color_ratios(monkeypatch, shape):
    monkeypatch.setattr(p, "LSC_K", 1.0)
    source = np.broadcast_to(
        np.array([0.2, 0.4, 0.8], np.float32), (*shape, 3)
    ).copy()
    result = p.reverse_lsc(source)
    np.testing.assert_allclose(result, result[::-1], atol=1e-7)
    np.testing.assert_allclose(result, result[:, ::-1], atol=1e-7)
    np.testing.assert_allclose(result[0, 0], source[0, 0] / 3)
    np.testing.assert_allclose(result[..., 1], result[..., 0] * 2)
    np.testing.assert_allclose(result[..., 2], result[..., 0] * 4)
    assert np.all(result > 0)
    assert np.all(result <= source)
    if shape == (5, 7):
        np.testing.assert_array_equal(result[2, 3], source[2, 3])


def test_zero_lsc_strength_is_identity(monkeypatch, color_image):
    monkeypatch.setattr(p, "LSC_K", 0)
    np.testing.assert_array_equal(p.reverse_lsc(color_image), color_image)


def test_white_balance_uses_bgr_gains_without_clipping(monkeypatch):
    monkeypatch.setattr(p, "WB_GAINS", {"R": 0.5, "G": 2, "B": 4})
    source = np.array([[[0.8, 0.6, 0.9], [0, 0, 0]]], np.float32)
    result = p.reverse_white_balance(source)
    np.testing.assert_allclose(result, [[[0.2, 0.3, 1.8], [0, 0, 0]]])
    np.testing.assert_allclose(result * [4, 2, 0.5], source)


def test_ccm_inverts_asymmetric_rgb_matrix_in_bgr_order(monkeypatch):
    matrix = np.array(
        [[1.2, -0.15, -0.05], [-0.1, 1.15, -0.05], [-0.02, -0.18, 1.2]],
        np.float32,
    )
    monkeypatch.setattr(p, "CCM", matrix)
    camera_rgb = np.array([[[-0.1, 0.4, 1.2], [0.7, 0.2, 0.1]]], np.float32)
    output_bgr = (camera_rgb @ matrix.T)[..., ::-1].copy()
    recovered = p.reverse_ccm(output_bgr)
    np.testing.assert_allclose(recovered, camera_rgb[..., ::-1], atol=2e-7)


def test_singular_ccm_raises(monkeypatch, color_image):
    monkeypatch.setattr(p, "CCM", np.zeros((3, 3)))
    with pytest.raises(np.linalg.LinAlgError):
        p.reverse_ccm(color_image)


def test_tone_mapping_endpoints_midtones_and_round_trip():
    source = np.array([[[0, 128, 255], [64, 192, 32]]], np.uint8)
    result = p.reverse_tone_mapping(source)
    assert result.dtype == np.float32
    np.testing.assert_allclose(
        result[0, 0], [0, (128 / 255) ** p.TONE_MAGIC_NUMBER, 1]
    )
    restored = np.rint(result ** (1 / p.TONE_MAGIC_NUMBER) * 255).astype(
        np.uint8
    )
    np.testing.assert_array_equal(restored, source)


def test_tone_mapping_honors_configured_exponent(monkeypatch):
    monkeypatch.setattr(p, "TONE_MAGIC_NUMBER", 1)
    source = np.array([[[0, 51, 255]]], np.uint8)
    np.testing.assert_allclose(p.reverse_tone_mapping(source), [[[0, 0.2, 1]]])

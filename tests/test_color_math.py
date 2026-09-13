"""Independent anchors and round trips for the frozen numeric color protocol."""

import math

import pytest

from baseline.color_math import (
    hsl_to_rgb,
    oklab_to_linear_rgb,
    oklch_to_oklab,
    rgb_to_hsl,
    rgb_to_oklab,
    rgb_to_oklch,
)


@pytest.mark.parametrize("rgb,expected", [
    ((0, 0, 0), (0, 0, 0)),
    ((255, 255, 255), (1, 0, 0)),
    ((255, 0, 0), (0.62795536, 0.22486306, 0.12584630)),
    ((0, 255, 0), (0.86643961, -0.23388757, 0.17949848)),
    ((0, 0, 255), (0.45201372, -0.03245698, -0.31152815)),
])
def test_srgb_primary_anchors(rgb, expected):
    assert rgb_to_oklab(rgb) == pytest.approx(expected, abs=1e-7)


@pytest.mark.parametrize("rgb,expected", [
    ((255, 0, 0), {"h": 0, "s": 100, "l": 50}),
    ((0, 255, 0), {"h": 120, "s": 100, "l": 50}),
    ((0, 0, 255), {"h": 240, "s": 100, "l": 50}),
    ((0, 255, 255), {"h": 180, "s": 100, "l": 50}),
    ((128, 128, 128), {"h": 0, "s": 0, "l": 128 / 255 * 100}),
    ((255, 255, 255), {"h": 0, "s": 0, "l": 100}),
    ((0, 0, 0), {"h": 0, "s": 0, "l": 0}),
])
def test_hsl_css_units_and_achromatic_convention(rgb, expected):
    assert rgb_to_hsl(rgb) == pytest.approx(expected, abs=1e-10)


def test_reconstruction_round_trips_cover_channels_and_transfer_breakpoint():
    for r in [0, 1, 10, 11, 64, 128, 254, 255]:
        for g in [0, 73, 128, 255]:
            for b in [0, 11, 180, 255]:
                rgb = (r, g, b)
                hsl = rgb_to_hsl(rgb)
                assert hsl_to_rgb(**hsl) == pytest.approx(rgb, abs=1e-8)
                lab = rgb_to_oklab(rgb)
                linear = oklab_to_linear_rgb(lab)
                expected = tuple(
                    v / 255 / 12.92 if v / 255 <= 0.04045
                    else ((v / 255 + 0.055) / 1.055) ** 2.4
                    for v in rgb
                )
                assert linear == pytest.approx(expected, abs=3e-7)
                lch = rgb_to_oklch(rgb)
                assert oklch_to_oklab(**lch) == pytest.approx(lab, abs=1e-7)


def test_hue_wraps_in_both_reconstructions():
    assert hsl_to_rgb(1, 70, 50) == pytest.approx(hsl_to_rgb(361, 70, 50))
    assert hsl_to_rgb(-1, 70, 50) == pytest.approx(hsl_to_rgb(359, 70, 50))
    assert oklch_to_oklab(0.6, 0.2, -1) == pytest.approx(oklch_to_oklab(0.6, 0.2, 359))


def test_gray_hue_is_canonical_and_does_not_amplify_matrix_noise():
    for channel in [0, 1, 128, 255]:
        lch = rgb_to_oklch((channel, channel, channel))
        assert lch["c"] == 0
        assert lch["h"] == 0


def test_out_of_gamut_prediction_remains_unclipped():
    lab = oklch_to_oklab(0.7, 0.5, 30)
    linear = oklab_to_linear_rgb(lab)
    assert max(linear) > 1
    assert min(linear) < 0
    assert all(math.isfinite(value) for value in linear)


def test_gamma_encoded_middle_gray_is_not_linear_middle_gray():
    l, a, b = rgb_to_oklab((128, 128, 128))
    assert l == pytest.approx(0.5998708, abs=1e-7)
    assert abs(a) < 1e-7 and abs(b) < 1e-7

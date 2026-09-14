"""Checks for the separate arithmetic and historical reference-free control."""
import pytest

from scripts.audit_publication import independent_distance, ordered_distractor_candidates


@pytest.mark.parametrize("hue, rgb", [(0, [255, 0, 0]), (60, [255, 255, 0]),
                                     (120, [0, 255, 0]), (180, [0, 255, 255]),
                                     (240, [0, 0, 255]), (300, [255, 0, 255])])
def test_independent_hsl_equations_reconstruct_six_primary_secondary_colors(hue, rgb):
    assert independent_distance("hsl", {"h": hue, "s": 100, "l": 50}, rgb) == 0
    assert independent_distance("hsl", {"h": hue + 720, "s": 100, "l": 50}, rgb) == 0


def test_independent_numeric_audit_keeps_out_of_gamut_oklch_unclipped():
    assert independent_distance("oklch", {"l": 0.5, "c": 1, "h": 0}, [128, 128, 128]) > 1


def test_order_shortcut_detects_unique_and_ambiguous_targets_without_reference():
    assert ordered_distractor_candidates([[20] * 3, [10] * 3, [30] * 3, [40] * 3]) == [0]
    assert ordered_distractor_candidates([[10] * 3, [20] * 3, [30] * 3, [40] * 3]) == [1, 2]
    assert ordered_distractor_candidates([[40] * 3, [20] * 3, [30] * 3, [10] * 3]) == [1, 2]

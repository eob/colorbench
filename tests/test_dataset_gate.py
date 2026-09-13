import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw
import pytest

from baseline.protocol import get_prompt


def gate():
    assert importlib.util.find_spec("baseline.validate_dataset") is not None, "Independent image evidence gate is missing"
    return importlib.import_module("baseline.validate_dataset")


def test_independent_dataset_gate_is_available():
    assert callable(gate().require_valid_dataset)


@pytest.fixture
def manifest(tmp_path):
    font = Path(__file__).parents[1] / "src/assets/DejaVuSans.ttf"
    (tmp_path / "fonts").mkdir()
    shutil.copyfile(font, tmp_path / "fonts/DejaVuSans.ttf")
    image = Image.new("RGB", (800, 640), (238, 238, 238))
    draw = ImageDraw.Draw(image)
    regions = []
    colors = [(192, 64, 80), (192, 64, 80), (100, 120, 130), (30, 50, 70), (60, 150, 90)]
    for i, rgb in enumerate(colors):
        x, y, size = (100 + i * 120, 200, 80)
        draw.rectangle((x, y, x + size - 1, y + size - 1), fill=rgb)
        regions.append(dict(role="target" if i == 0 else "option", id="R" if i == 0 else "ABCD"[i - 1],
                            x=x, y=y, width=size, height=size, rgb=list(rgb),
                            pixelSha256=hashlib.sha256(image.crop((x, y, x + size, y + size)).tobytes()).hexdigest()))
    image.save(tmp_path / "sample.png")
    item = dict(taskId="fixture-1", family="matching", groupId="fixture", imageFilename="sample.png",
                imageSha256=hashlib.sha256((tmp_path / "sample.png").read_bytes()).hexdigest(),
                groundTruth={"choice": "A"}, prompt=get_prompt("matching"),
                design={"axis": "lightness", "difficulty": "wide", "sourceRgb": [192, 64, 80],
                        "intendedSeparation": 0.0020769128407567283},
                rendered=dict(width=800, height=640, browserVersion="145.0", platform="linux", colorSpace="srgb",
                              viewport=dict(width=800, height=640, deviceScaleFactor=1), regions=regions,
                              font=dict(path="fonts/DejaVuSans.ttf", sha256=hashlib.sha256(font.read_bytes()).hexdigest(),
                                        family="DejaVu Sans", sizePx=16, lineHeightPx=24,
                                        platformFonts=[dict(familyName="DejaVu Sans", isCustomFont=True, glyphCount=10)])))
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps([item]))
    return path


def test_valid_partial_fixture_is_checked_but_not_publishable_full_pilot(manifest):
    assert gate().validate_dataset(manifest, require_complete=False)["valid"]
    assert not gate().validate_dataset(manifest)["valid"]


@pytest.mark.parametrize("mutation", [
    lambda item: item["groundTruth"].update(choice="B"),
    lambda item: item.update(prompt=item["prompt"] + " Answer A."),
    lambda item: item["rendered"]["regions"][0].update(rgb=[0, 0, 0]),
    lambda item: item["rendered"]["regions"][1].update(x=-1),
    lambda item: item["rendered"]["regions"][1].update(id="B"),
    lambda item: item.update(imageSha256="0" * 64),
    lambda item: item["rendered"]["font"].update(sha256="0" * 64),
    lambda item: item.update(imageFilename="../sample.png"),
])
def test_dataset_gate_rejects_forged_targets_pixels_prompts_and_paths(manifest, mutation):
    items = json.loads(manifest.read_text())
    mutation(items[0])
    manifest.write_text(json.dumps(items))
    assert not gate().validate_dataset(manifest, require_complete=False)["valid"]


def test_missing_image_never_receives_a_dataset_fingerprint(manifest):
    from baseline.runner import dataset_fingerprint
    from baseline.evaluator import load_manifest
    items = load_manifest(manifest)
    (manifest.parent / "sample.png").unlink()
    with pytest.raises(FileNotFoundError):
        dataset_fingerprint(items)


def test_color_profile_cannot_silently_change_pixel_interpretation(manifest):
    path = manifest.parent / "sample.png"
    with Image.open(path) as image:
        rgb = image.convert("RGB")
    rgb.save(path, icc_profile=b"unverified display profile")
    items = json.loads(manifest.read_text())
    items[0]["imageSha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(items))
    assert not gate().validate_dataset(manifest, require_complete=False)["valid"]


def _paint(builder, tmp_path, name, family, paint, regions, ground_truth, prompt, design, group="fixture"):
    font = Path(__file__).parents[1] / "src/assets/DejaVuSans.ttf"
    (tmp_path / "fonts").mkdir(exist_ok=True)
    shutil.copyfile(font, tmp_path / "fonts/DejaVuSans.ttf")
    image = Image.new("RGB", (800, 640), (238, 238, 238))
    paint(ImageDraw.Draw(image))
    for region in regions:
        crop = image.crop((region["x"], region["y"], region["x"] + region["width"], region["y"] + region["height"]))
        region["pixelSha256"] = hashlib.sha256(crop.tobytes()).hexdigest()
    image.save(tmp_path / name)
    item = dict(taskId=name.replace(".png", ""), family=family, groupId=group, imageFilename=name,
                imageSha256=hashlib.sha256((tmp_path / name).read_bytes()).hexdigest(),
                groundTruth=ground_truth, prompt=prompt, design=design,
                rendered=dict(width=800, height=640, browserVersion="145.0", platform="linux", colorSpace="srgb",
                              viewport=dict(width=800, height=640, deviceScaleFactor=1), regions=regions,
                              font=dict(path="fonts/DejaVuSans.ttf", sha256=hashlib.sha256(font.read_bytes()).hexdigest(),
                                        family="DejaVu Sans", sizePx=16, lineHeightPx=24,
                                        platformFonts=[dict(familyName="DejaVu Sans", isCustomFont=True, glyphCount=10)])))
    builder.append(item)
    return item


def _write_manifest(tmp_path, builder):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(builder))
    return path


def _flat(draw, x, y, w, h, rgb):
    draw.rectangle((x, y, x + w - 1, y + h - 1), fill=tuple(rgb))


def test_samediff_accepts_matching_equality_and_mapping(tmp_path):
    from baseline.protocol import get_prompt
    builder = []
    same_rgb = [150, 90, 90]
    _paint(builder, tmp_path, "same.png", "samediff",
           lambda draw: (_flat(draw, 220, 330, 84, 84, same_rgb), _flat(draw, 496, 330, 84, 84, same_rgb)),
           [dict(role="option", id="A", x=220, y=330, width=84, height=84, rgb=same_rgb),
            dict(role="option", id="B", x=496, y=330, width=84, height=84, rgb=same_rgb)],
           {"choice": "A"}, get_prompt("samediff", "sameA"),
           {"axis": "identity", "difficulty": "same", "direction": "sameA", "same": True, "intendedSeparation": 0})
    _paint(builder, tmp_path, "diff.png", "samediff",
           lambda draw: (_flat(draw, 220, 330, 84, 84, [156, 145, 77]), _flat(draw, 496, 330, 84, 84, [150, 147, 79])),
           [dict(role="option", id="A", x=220, y=330, width=84, height=84, rgb=[156, 145, 77]),
            dict(role="option", id="B", x=496, y=330, width=84, height=84, rgb=[150, 147, 79])],
           {"choice": "A"}, get_prompt("samediff", "sameB"),
           {"axis": "hue", "difficulty": "narrow", "direction": "sameB", "same": False, "intendedSeparation": 6})
    assert gate().validate_dataset(_write_manifest(tmp_path, builder), require_complete=False)["valid"]


@pytest.mark.parametrize("mutation,fragment", [
    (lambda item: item["groundTruth"].update(choice="B"), "Ground truth disagrees"),
    (lambda item: item["design"].update(same=False), "equality flag"),
    (lambda item: (item["design"].update(direction="sameB"),
                   item.update(prompt=get_prompt("samediff", "sameB"))), "Ground truth disagrees"),
])
def test_samediff_rejects_wrong_choice_flag_or_mapping(tmp_path, mutation, fragment):
    from baseline.protocol import get_prompt
    builder = []
    same_rgb = [150, 90, 90]
    item = _paint(builder, tmp_path, "same.png", "samediff",
                  lambda draw: (_flat(draw, 220, 330, 84, 84, same_rgb), _flat(draw, 496, 330, 84, 84, same_rgb)),
                  [dict(role="option", id="A", x=220, y=330, width=84, height=84, rgb=same_rgb),
                   dict(role="option", id="B", x=496, y=330, width=84, height=84, rgb=same_rgb)],
                  {"choice": "A"}, get_prompt("samediff", "sameA"),
                  {"axis": "identity", "difficulty": "same", "direction": "sameA", "same": True, "intendedSeparation": 0})
    mutation(item)
    report = gate().validate_dataset(_write_manifest(tmp_path, builder), require_complete=False)
    assert not report["valid"]
    assert any(fragment in error for error in report["errors"])


def test_context_checks_interior_match_and_surround_probes(tmp_path):
    from baseline.protocol import get_prompt
    builder = []
    surround = {"A": [60, 60, 62], "B": [232, 224, 208], "C": [196, 64, 48], "D": [44, 140, 150]}
    target = [150, 110, 110]
    fills = {"A": [150, 110, 130], "B": target, "C": [150, 130, 110], "D": [130, 110, 110]}
    boxes = {"A": (84, 348), "B": (258, 348), "C": (432, 348), "D": (606, 348)}

    def paint(draw):
        _flat(draw, 358, 140, 84, 84, target)
        for label, (x, y) in boxes.items():
            _flat(draw, x, y, 108, 108, surround[label])
            _flat(draw, x + 12, y + 12, 84, 84, fills[label])

    regions = [dict(role="target", id="R", x=358, y=140, width=84, height=84, rgb=target)]
    regions += [dict(role="option", id=label, x=x + 12, y=y + 12, width=84, height=84, rgb=fills[label])
                for label, (x, y) in boxes.items()]
    design = {"axis": "lightness", "difficulty": "mid", "intendedSeparation": 0.006257038803287318,
              "intendedHue": 25, "sourceRgb": target, "surround": surround,
              "reference": {"kind": "surround-shift", "neutralSurround": [238, 238, 238]}}
    _paint(builder, tmp_path, "ctx.png", "context", paint, regions, {"choice": "B"},
           get_prompt("context"), design)
    assert gate().validate_dataset(_write_manifest(tmp_path, builder), require_complete=False)["valid"]
    items = json.loads((tmp_path / "manifest.json").read_text())
    items[0]["design"]["surround"]["A"] = [0, 0, 0]
    (tmp_path / "manifest.json").write_text(json.dumps(items))
    report = gate().validate_dataset(tmp_path / "manifest.json", require_complete=False)
    assert not report["valid"]
    assert any("Surround" in error for error in report["errors"])


def test_smallmatch_accepts_dot_and_frame_layouts(tmp_path):
    from baseline.protocol import get_prompt
    builder = []
    target = [150, 110, 110]
    dots = {"A": [150, 110, 130], "B": target, "C": [150, 130, 110], "D": [130, 110, 110]}
    dot_x = {"A": 128, "B": 302, "C": 476, "D": 650}
    _paint(builder, tmp_path, "dot.png", "smallmatch",
           lambda draw: ([_flat(draw, 390, 140, 20, 20, target)] +
                         [_flat(draw, dot_x[label], 392, 20, 20, rgb) for label, rgb in dots.items()] +
                         [_flat(draw, 380, 362, 40, 8, [32, 32, 32])]),
           [dict(role="target", id="R", x=390, y=140, width=20, height=20, rgb=target)] +
           [dict(role="option", id=label, x=dot_x[label], y=392, width=20, height=20, rgb=rgb)
            for label, rgb in dots.items()],
           {"choice": "B"}, get_prompt("smallmatch"),
           {"axis": "lightness", "difficulty": "mid", "layout": "dot",
            "intendedSeparation": 0.006257038803287318, "sourceRgb": target,
            "reference": {"kind": "small-region", "neutralSurround": [238, 238, 238]}})

    def frame_paint(draw):
        _flat(draw, 358, 140, 84, 84, [238, 238, 238])
        draw.rectangle((358, 140, 358 + 83, 140 + 83), outline=tuple(target), width=3)
        for i, (label, rgb) in enumerate(dots.items()):
            x = [96, 270, 444, 618][i]
            _flat(draw, x, 360, 84, 84, [238, 238, 238])
            draw.rectangle((x, 360, x + 83, 360 + 83), outline=tuple(rgb), width=3)
        _flat(draw, 380, 300, 40, 8, [32, 32, 32])

    frame_regions = [dict(role="target", id="R", x=358, y=140, width=84, height=84)]
    frame_regions += [dict(role="option", id=label, x=x, y=360, width=84, height=84)
                      for label, x in zip("ABCD", [96, 270, 444, 618])]
    _paint(builder, tmp_path, "frame.png", "smallmatch", frame_paint, frame_regions, {"choice": "B"},
           get_prompt("smallmatch"),
           {"axis": "test", "difficulty": "mid", "layout": "frame", "intendedSeparation": 0,
            "sourceRgb": target, "reference": {"kind": "small-region", "neutralSurround": [238, 238, 238]}})
    assert gate().validate_dataset(_write_manifest(tmp_path, builder), require_complete=False)["valid"]


def test_hue_thresholds_follow_the_recorded_minimum_separation():
    from baseline.protocol import get_prompt
    from PIL import Image as PilImage
    import tempfile, os
    tmp_path = Path(tempfile.mkdtemp())
    builder = []
    target = [185, 125, 124]
    options = {"A": [184, 126, 114], "B": target, "C": [108, 157, 121], "D": [127, 141, 190]}
    xs = {"A": 96, "B": 270, "C": 444, "D": 618}
    _paint(builder, tmp_path, "hue12.png", "hue",
           lambda draw: ([_flat(draw, 358, 140, 84, 84, target)] +
                         [_flat(draw, xs[label], 360, 84, 84, rgb) for label, rgb in options.items()]),
           [dict(role="target", id="R", x=358, y=140, width=84, height=84, rgb=target)] +
           [dict(role="option", id=label, x=xs[label], y=360, width=84, height=84, rgb=rgb)
            for label, rgb in options.items()],
           {"choice": "B"}, get_prompt("hue"),
           {"axis": "hue", "difficulty": "fixed-lightness-chroma", "intendedSeparation": 12, "intendedHue": 20,
            "sourceRgb": target, "reference": {"kind": "hue-reference", "minimumDistractorDegrees": 12},
            "humanAgreementMeasured": False})
    assert gate().validate_dataset(_write_manifest(tmp_path, builder), require_complete=False)["valid"]
    items = json.loads((tmp_path / "manifest.json").read_text())
    items[0]["design"]["reference"]["minimumDistractorDegrees"] = 170
    (tmp_path / "manifest.json").write_text(json.dumps(items))
    report = gate().validate_dataset(tmp_path / "manifest.json", require_complete=False)
    assert not report["valid"]
    assert any("Hue reference is ambiguous" in error for error in report["errors"])


def test_complete_counts_and_crossing_rules_pin_the_248_question_release():
    module = gate()
    assert module.COMPLETE_FAMILY_COUNTS == {
        "matching": 48, "binding": 48, "lightness": 16, "chroma": 16, "hue": 16, "gradient": 8,
        "samediff": 16, "context": 16, "smallmatch": 16, "rgb": 16, "hsl": 16, "oklch": 16}
    assert sum(module.COMPLETE_FAMILY_COUNTS.values()) == 248
    assert module.SWEEP_SEPARATIONS == {
        "matching": {"lightness": [0.08, 0.04, 0.02, 0.01], "chroma": [0.025, 0.012, 0.007, 0.004],
                     "hue": [35, 15, 8, 4]},
        "binding": {"lightness": [0.08, 0.04, 0.02, 0.01], "chroma": [0.025, 0.012, 0.007, 0.004],
                    "hue": [35, 15, 8, 4]},
        "lightness": {"lightness": [0.10, 0.05, 0.02, 0.01]},
        "chroma": {"chroma": [0.06, 0.03, 0.015, 0.008]},
        "hue": {"hue": [70, 30, 12, 6]}}
    items = []
    for axis, seps in module.SWEEP_SEPARATIONS["matching"].items():
        for sep in seps:
            for choice in "ABCD":
                items.append({"taskId": f"m-{axis}-{sep}-{choice}", "family": "matching",
                              "groundTruth": {"choice": choice},
                              "design": {"axis": axis, "intendedSeparation": sep}})
    for sep in module.SWEEP_SEPARATIONS["lightness"]["lightness"]:
        for direction in ("lighter", "darker"):
            for choice in "AB":
                items.append({"taskId": f"l-{sep}-{direction}-{choice}", "family": "lightness",
                              "groundTruth": {"choice": choice},
                              "design": {"axis": "lightness", "intendedSeparation": sep, "direction": direction}})
    for sep in module.SWEEP_SEPARATIONS["hue"]["hue"]:
        for index, choice in enumerate("ABCD"):
            items.append({"taskId": f"h-{sep}-{choice}", "family": "hue",
                          "groundTruth": {"choice": choice},
                          "design": {"axis": "hue", "intendedSeparation": sep,
                                     "difficulty": "fixed-lightness-chroma" if index % 2 == 0 else "varying-lightness-chroma"}})
    for same in (True, False):
        for direction in ("sameA", "sameB"):
            for index in range(4):
                items.append({"taskId": f"s-{same}-{direction}-{index}", "family": "samediff",
                              "groundTruth": {"choice": "A"},
                              "design": {"same": same, "direction": direction}})
    for hue in (25, 115, 205, 295):
        for choice in "ABCD":
            items.append({"taskId": f"c-{hue}-{choice}", "family": "context",
                          "groundTruth": {"choice": choice}, "design": {"intendedHue": hue}})
    for layout in ("dot", "frame"):
        for choice in "ABCD":
            for index in range(2):
                items.append({"taskId": f"t-{layout}-{choice}-{index}", "family": "smallmatch",
                              "groundTruth": {"choice": choice}, "design": {"layout": layout}})
    assert module.check_crossing(items) == []
    assert module.check_crossing(items[:-1]) != []
    broken = [dict(item, design={**item["design"], "intendedSeparation": 0.5}) for item in items[:1]] + items[1:]
    assert module.check_crossing(broken) != []


def test_design_direction_and_layout_are_whitelisted_per_family(tmp_path):
    builder = []
    rgb = [150, 90, 90]
    _paint(builder, tmp_path, "m.png", "matching",
           lambda draw: (_flat(draw, 358, 140, 84, 84, rgb), _flat(draw, 96, 360, 84, 84, rgb),
                         _flat(draw, 270, 360, 84, 84, [1, 2, 3]), _flat(draw, 444, 360, 84, 84, [4, 5, 6]),
                         _flat(draw, 618, 360, 84, 84, [7, 8, 9])),
           [dict(role="target", id="R", x=358, y=140, width=84, height=84, rgb=rgb)] +
           [dict(role="option", id=label, x=x, y=360, width=84, height=84, rgb=color)
            for label, x, color in zip("ABCD", [96, 270, 444, 618],
                                       [rgb, [1, 2, 3], [4, 5, 6], [7, 8, 9]])],
           {"choice": "A"}, get_prompt("matching"),
           {"axis": "test", "difficulty": "wide", "direction": "leak-split", "intendedSeparation": 0})
    report = gate().validate_dataset(_write_manifest(tmp_path, builder), require_complete=False)
    assert not report["valid"]
    assert any("direction" in error and "matching" in error for error in report["errors"])


def test_samediff_axis_is_validated_on_same_and_different_pairs(tmp_path):
    from baseline.protocol import get_prompt
    builder = []
    rgb = [150, 90, 90]
    _paint(builder, tmp_path, "same.png", "samediff",
           lambda draw: (_flat(draw, 220, 330, 84, 84, rgb), _flat(draw, 496, 330, 84, 84, rgb)),
           [dict(role="option", id="A", x=220, y=330, width=84, height=84, rgb=rgb),
            dict(role="option", id="B", x=496, y=330, width=84, height=84, rgb=rgb)],
           {"choice": "A"}, get_prompt("samediff", "sameA"),
           {"axis": "nonsense-axis", "difficulty": "same", "direction": "sameA", "same": True,
            "intendedSeparation": 0})
    report = gate().validate_dataset(_write_manifest(tmp_path, builder), require_complete=False)
    assert not report["valid"]
    assert any("axis" in error for error in report["errors"])


def test_exact_match_families_verify_decoded_nearest_gaps(tmp_path):
    builder = []
    target = [107, 152, 158]
    near = [107, 152, 161]
    _paint(builder, tmp_path, "gap.png", "matching",
           lambda draw: (_flat(draw, 358, 140, 84, 84, target), _flat(draw, 96, 360, 84, 84, target),
                         _flat(draw, 270, 360, 84, 84, near), _flat(draw, 444, 360, 84, 84, [4, 5, 6]),
                         _flat(draw, 618, 360, 84, 84, [7, 8, 9])),
           [dict(role="target", id="R", x=358, y=140, width=84, height=84, rgb=target)] +
           [dict(role="option", id=label, x=x, y=360, width=84, height=84, rgb=color)
            for label, x, color in zip("ABCD", [96, 270, 444, 618],
                                       [target, near, [4, 5, 6], [7, 8, 9]])],
           {"choice": "A"}, get_prompt("matching"),
           {"axis": "hue", "difficulty": "narrow", "intendedSeparation": 8,
            "intendedTargetOklch": {"l": 0.65, "c": 0.05, "h": 205}})
    report = gate().validate_dataset(_write_manifest(tmp_path, builder), require_complete=False)
    assert not report["valid"]
    assert any("decoded separation" in error for error in report["errors"])


def test_lightness_decoded_gap_must_match_the_recorded_separation(tmp_path):
    from baseline.protocol import get_prompt
    builder = []
    _paint(builder, tmp_path, "gap.png", "lightness",
           lambda draw: (_flat(draw, 220, 330, 84, 84, [120, 120, 120]),
                         _flat(draw, 496, 330, 84, 84, [180, 180, 180])),
           [dict(role="option", id="A", x=220, y=330, width=84, height=84, rgb=[120, 120, 120]),
            dict(role="option", id="B", x=496, y=330, width=84, height=84, rgb=[180, 180, 180])],
           {"choice": "B"}, get_prompt("lightness", "lighter"),
           {"axis": "lightness", "difficulty": "near", "direction": "lighter", "intendedHue": 0,
            "intendedSeparation": 0.01, "reference": {"kind": "dark-to-light", "colors": [[0, 0, 0]]},
            "decodedOptionOklch": []})
    report = gate().validate_dataset(_write_manifest(tmp_path, builder), require_complete=False)
    assert not report["valid"]
    assert any("decoded separation" in error for error in report["errors"])

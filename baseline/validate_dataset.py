"""Independently check decoded ColorBench stimuli before any paid request."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath

from PIL import Image, ImageDraw

from baseline.color_math import rgb_to_oklch
from baseline.direct_controls import COMPLETE_COUNTS, CONTROL_VERSION, check_direct_controls
from baseline.evaluator import load_manifest
from baseline.protocol import CHOICE_FAMILIES, FAMILIES, NUMERIC_FAMILIES, choice_labels

FONT_SHA256 = "abdc775b21b1bc470d50c97e790d276f2054b7504e56e5bd3e64f48d68582322"
VIEWPORT = {"width": 800, "height": 640, "deviceScaleFactor": 1}
COMPLETE_FAMILY_COUNTS = COMPLETE_COUNTS
SWEEP_SEPARATIONS = {
    "matching": {"lightness": [0.08, 0.04, 0.02, 0.01], "chroma": [0.025, 0.012, 0.007, 0.004],
                 "hue": [35, 15, 8, 4]},
    "binding": {"lightness": [0.08, 0.04, 0.02, 0.01], "chroma": [0.025, 0.012, 0.007, 0.004],
                "hue": [35, 15, 8, 4]},
    "lightness": {"lightness": [0.10, 0.05, 0.02, 0.01]},
    "chroma": {"chroma": [0.06, 0.03, 0.015, 0.008]},
    "hue": {"hue": [70, 30, 12, 6]}}
CONTEXT_HUES = [25, 115, 205, 295]
EXACT_MATCH_FAMILIES = ("matching", "binding", "gradient", "context", "smallmatch")
PAIR_DIRECTIONS = {"lightness": ("lighter", "darker"), "chroma": ("more", "less")}
ALLOWED_DIRECTIONS = {
    "lightness": ("lighter", "darker"), "chroma": ("more", "less"), "samediff": ("sameA", "sameB")}
ALLOWED_LAYOUTS = {"smallmatch": ("dot", "frame")}


def check_crossing(items):
    """Pin the pilot's lesson: every separation at every answer position."""
    errors = []
    by_family = defaultdict(list)
    for item in items:
        by_family[item["family"]].append(item)
    reference_crossed = any(row["design"].get("optionSetId") for row in items)
    for family, axes in SWEEP_SEPARATIONS.items():
        rows = by_family.get(family, [])
        if not rows:
            continue
        if family in PAIR_DIRECTIONS and all(row["design"].get("controlVersion") == CONTROL_VERSION for row in rows):
            # Decoded chain graphs and whole-image single-patch bounds replace
            # the historical fixed-center separation crossing.
            continue
        pair = family in PAIR_DIRECTIONS
        observed = {(row["design"].get("axis"), row["design"].get("intendedSeparation"),
                     row["design"].get("direction")) for row in rows} if pair else {
                         (row["design"].get("axis"), row["design"].get("intendedSeparation")) for row in rows}
        expected = {(axis, sep, direction) for axis, seps in axes.items() for sep in seps
                    for direction in PAIR_DIRECTIONS[family]} if pair else {
                        (axis, sep) for axis, seps in axes.items() for sep in seps}
        if observed != expected:
            errors.append(f"{family} separation cells differ from the frozen sweep")
            continue
        cells = defaultdict(list)
        for row in rows:
            key = (row["design"].get("axis"), row["design"].get("intendedSeparation"))
            if pair:
                key += (row["design"].get("direction"),)
            elif family == "hue" and reference_crossed:
                key += (row["design"].get("difficulty"),)
            cells[key].append(row["groundTruth"]["choice"])
        want = ["A", "B"] if pair else ["A", "B", "C", "D"]
        for cell, choices in cells.items():
            if sorted(choices) != want:
                errors.append(f"{family} cell {cell} is not counterbalanced across positions")
    hues = by_family.get("hue", [])
    if hues:
        per_sep = defaultdict(Counter)
        for row in hues:
            per_sep[row["design"].get("intendedSeparation")][row["design"].get("difficulty")] += 1
        for sep, counts in per_sep.items():
            if counts != Counter({"fixed-lightness-chroma": 4 if reference_crossed else 2,
                                  "varying-lightness-chroma": 4 if reference_crossed else 2}):
                errors.append(f"hue separation {sep} is not balanced across fixed/varying contexts")
    sames = by_family.get("samediff", [])
    if sames:
        cells = Counter((row["design"].get("same"), row["design"].get("direction")) for row in sames)
        if set(cells) != {(True, "sameA"), (True, "sameB"), (False, "sameA"), (False, "sameB")} or len(set(cells.values())) != 1:
            errors.append("samediff is not crossed across equality and answer mapping")
    contexts = by_family.get("context", [])
    if contexts:
        if {row["design"].get("intendedHue") for row in contexts} != set(CONTEXT_HUES):
            errors.append("context hues differ from the frozen set")
        else:
            per_hue = defaultdict(list)
            for row in contexts:
                per_hue[row["design"].get("intendedHue")].append(row["groundTruth"]["choice"])
            for hue, choices in per_hue.items():
                repeats = 5 if all(row["design"].get("controlVersion") == CONTROL_VERSION for row in contexts) else 1
                if sorted(choices) != sorted(list("ABCD") * repeats):
                    errors.append(f"context hue {hue} is not counterbalanced across positions")
    smalls = by_family.get("smallmatch", [])
    if smalls:
        cells = Counter((row["design"].get("layout"), row["groundTruth"]["choice"]) for row in smalls)
        repeats = 8 if all(row["design"].get("controlVersion") == CONTROL_VERSION for row in smalls) else 2
        if {layout for layout, _ in cells} != {"dot", "frame"} or len(cells) != 8 or any(value != repeats for value in cells.values()):
            errors.append("smallmatch is not crossed across layout and position")
    return errors


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _hash(data):
    return hashlib.sha256(data).hexdigest()


def _region(image, region):
    _require(isinstance(region, dict), "Malformed pixel region")
    _require(region.get("role") in ("target", "option", "reference") and isinstance(region.get("id"), str), "Invalid region role or ID")
    keys = ("x", "y", "width", "height")
    _require(all(type(region.get(key)) is int for key in keys), "Region geometry requires integers")
    x, y, width, height = (region[key] for key in keys)
    _require(x >= 0 and y >= 0 and width > 0 and height > 0 and x + width <= image.width and y + height <= image.height,
             "Region falls outside the image")
    crop = image.crop((x, y, x + width, y + height))
    _require(_hash(crop.tobytes()) == region.get("pixelSha256"), "Region pixel hash differs from decoded pixels")
    rgb = region.get("rgb")
    if rgb is not None:
        _require(isinstance(rgb, list) and len(rgb) == 3 and all(type(v) is int and 0 <= v <= 255 for v in rgb), "Invalid region RGB")
        _require(crop.getextrema() == tuple((channel, channel) for channel in rgb), "Region is not the claimed uniform color")
    return crop


def _separation_matches(axis, coordinates, intended):
    if type(intended) not in (int, float) or axis not in ("lightness", "chroma", "hue"):
        return False
    labels = sorted(coordinates)
    if axis == "hue":
        gap = abs((coordinates[labels[0]]["h"] - coordinates[labels[1]]["h"] + 180) % 360 - 180)
        return abs(gap - intended) <= max(2.5, .35 * intended)
    dimension = "l" if axis == "lightness" else "c"
    gap = abs(coordinates[labels[0]][dimension] - coordinates[labels[1]][dimension])
    return abs(gap - intended) <= max(.01, .35 * intended)


def _item(item, directory):
    image_path = Path(item["imagePath"])
    _require(_hash(image_path.read_bytes()) == item.get("imageSha256"), "Image hash differs from manifest")
    rendered = item.get("rendered")
    _require(isinstance(rendered, dict), "Missing rendered evidence")
    _require(rendered.get("viewport") == VIEWPORT and rendered.get("width") == 800 and rendered.get("height") == 640,
             "Rendered viewport must be 800x640 at DPR 1")
    _require(rendered.get("colorSpace") == "srgb", "The pilot requires the sRGB pipeline")
    _require(all(isinstance(rendered.get(key), str) and rendered[key] for key in ("browserVersion", "platform")), "Missing renderer provenance")
    font = rendered.get("font")
    _require(isinstance(font, dict), "Missing font evidence")
    relative = font.get("path")
    _require(isinstance(relative, str) and not PurePosixPath(relative).is_absolute()
             and ".." not in PurePosixPath(relative).parts and "\\" not in relative, "Invalid font path")
    font_path = directory / relative
    _require(not font_path.is_symlink() and font_path.is_file(), "Missing bundled font")
    _require(font.get("sha256") == FONT_SHA256 == _hash(font_path.read_bytes()), "Reference font differs from pinned DejaVu Sans")
    _require(font.get("sizePx") == 16 and font.get("lineHeightPx") == 24 and font.get("family") == "DejaVu Sans", "Invalid font reference")
    actual_fonts = font.get("platformFonts")
    _require(isinstance(actual_fonts, list) and actual_fonts and all(isinstance(row, dict) and row.get("isCustomFont") is True
             and row.get("familyName") == "DejaVu Sans" and type(row.get("glyphCount")) is int and row["glyphCount"] > 0
             for row in actual_fonts), "Actual glyphs must use the bundled font")
    with Image.open(image_path) as source:
        _require(source.format == "PNG" and source.size == (800, 640), "Invalid image format or dimensions")
        _require(source.mode in ("RGB", "RGBA"), "Unexpected decoded pixel mode")
        if source.mode == "RGBA":
            _require(source.getchannel("A").getextrema() == (255, 255), "Stimulus PNG must be opaque")
        _require(not source.info, "Pilot PNGs must have no embedded profiles, transfer overrides, or text metadata")
        image = source.convert("RGB")
    regions = rendered.get("regions")
    _require(isinstance(regions, list) and regions, "Missing pixel regions")
    _require(len({(r.get("role"), r.get("id")) for r in regions if isinstance(r, dict)}) == len(regions), "Duplicate region identity")
    crops = {(region["role"], region["id"]): _region(image, region) for region in regions}
    options = {region["id"]: region for region in regions if region["role"] == "option"}
    targets = [region for region in regions if region["role"] == "target"]
    family = item["family"]
    _require(item["design"].get("direction") in ALLOWED_DIRECTIONS.get(family, (None,)),
             f"Design direction is not allowed for {family}")
    _require(item["design"].get("layout") in ALLOWED_LAYOUTS.get(family, (None,)),
             f"Design layout is not allowed for {family}")
    _require(set(options) == (set(choice_labels(family)) if family in CHOICE_FAMILIES else set()), "Option count or labels disagree with family")
    _require(len(targets) == (0 if family in ("lightness", "chroma", "samediff") else 1), "Unexpected target count")
    if family in NUMERIC_FAMILIES:
        _require(targets[0].get("rgb") == item["groundTruth"]["rgb"], "Numeric target differs from decoded pixels")
    elif family in EXACT_MATCH_FAMILIES:
        target = crops[("target", targets[0]["id"])]
        matches = [label for label in options if crops[("option", label)].size == target.size and crops[("option", label)].tobytes() == target.tobytes()]
        _require(matches == [item["groundTruth"]["choice"]], "Matching target must have exactly one correct option")
        _require(len({crops[("option", label)].tobytes() for label in options}) == len(options), "Distractor colors must remain distinct")
        if family in ("matching", "binding", "context") or item["design"].get("layout") == "dot":
            axis = item["design"].get("axis")
            intended = item["design"].get("intendedSeparation")
            _require(axis in ("lightness", "chroma", "hue") and type(intended) in (int, float),
                     "Exact-match sweep items must record their axis and separation")
            center = rgb_to_oklch(targets[0]["rgb"])
            gaps = []
            for label in options:
                if label in matches:
                    continue
                value = rgb_to_oklch(options[label]["rgb"])
                gaps.append(abs((value["h"] - center["h"] + 180) % 360 - 180) if axis == "hue"
                            else abs(value["l" if axis == "lightness" else "c"] - center["l" if axis == "lightness" else "c"]))
            tolerance = max(2.5, .25 * intended) if axis == "hue" else max(.01, .35 * intended)
            _require(abs(min(gaps) - intended) <= tolerance,
                     "Matching decoded separation differs from the recorded separation")
        if family == "context":
            surround = item["design"].get("surround")
            _require(isinstance(surround, dict) and set(surround) == set(options)
                     and all(isinstance(value, list) and len(value) == 3
                             and all(type(channel) is int and 0 <= channel <= 255 for channel in value)
                             for value in surround.values()), "Context surround must record one RGB color per option")
            for label, region in options.items():
                probe = image.getpixel((region["x"] - 6, region["y"] - 6))
                _require(list(probe) == surround[label], f"Surround ring pixels differ from the recorded surround at {label}")
    elif family == "samediff":
        _require(all("rgb" in region for region in options.values()), "Color-coordinate tasks require flat option colors")
        equal = crops[("option", "A")].tobytes() == crops[("option", "B")].tobytes()
        flag = item["design"].get("same")
        _require(type(flag) is bool and flag == equal, "Same-different equality flag disagrees with decoded pixels")
        direction = item["design"].get("direction")
        _require(direction in ("sameA", "sameB"), "Same-different mapping must be recorded")
        intended = item["design"].get("intendedSeparation")
        axis = item["design"].get("axis")
        if equal:
            _require(axis == "identity", "Identical patches must record the identity axis")
            _require(intended == 0, "Identical patches must record a zero intended separation")
        else:
            _require(axis in ("lightness", "chroma", "hue"), "Differing patches must record a color axis")
            coordinates = {label: rgb_to_oklch(region["rgb"]) for label, region in options.items()}
            _require(_separation_matches(axis, coordinates, intended),
                     "Same-different decoded separation differs from the recorded separation")
        same_choice = "A" if direction == "sameA" else "B"
        answer = same_choice if equal else ("B" if same_choice == "A" else "A")
        _require(answer == item["groundTruth"]["choice"], "Ground truth disagrees with decoded equality and mapping")
    else:
        _require(all("rgb" in region for region in options.values()), "Color-coordinate tasks require flat option colors")
        coordinates = {label: rgb_to_oklch(region["rgb"]) for label, region in options.items()}
        if family in ("lightness", "chroma"):
            dimension = "l" if family == "lightness" else "c"
            ordered = sorted(coordinates, key=lambda label: coordinates[label][dimension])
            gap = abs(coordinates[ordered[0]][dimension] - coordinates[ordered[-1]][dimension])
            _require(gap > .005, "Ordering gap vanished after rendering")
            _require(_separation_matches(family, coordinates, item["design"].get("intendedSeparation")),
                     "Ordering decoded separation differs from the recorded separation")
            high = item["design"].get("direction") in ("lighter", "more")
            answer = ordered[-1 if high else 0]
        else:
            target = rgb_to_oklch(targets[0]["rgb"])
            _require(target["c"] >= .02 and all(value["c"] >= .02 for value in coordinates.values()), "Hue target and options require chromatic colors")
            errors = {label: abs((value["h"] - target["h"] + 180) % 360 - 180) for label, value in coordinates.items()}
            ordered = sorted(errors, key=errors.get)
            reference = item["design"].get("reference") or {}
            minimum = reference.get("minimumDistractorDegrees")
            _require(type(minimum) in (int, float), "Hue reference must record its minimum distractor separation")
            _require(errors[ordered[0]] <= 1 and errors[ordered[1]] - errors[ordered[0]] >= 2.5
                     and abs(errors[ordered[1]] - minimum) <= max(2.5, .25 * minimum),
                     "Hue reference is ambiguous after rendering")
            answer = ordered[0]
        _require(answer == item["groundTruth"]["choice"], "Ground truth disagrees with decoded color coordinates")
    if targets and item["design"].get("sourceRgb") is not None:
        target_pixel = crops[("target", targets[0]["id"])].getpixel((0, 0))
        _require(list(target_pixel) == item["design"]["sourceRgb"], "Source RGB differs from decoded target")
    masked = image.copy()
    draw = ImageDraw.Draw(masked)
    for region in regions:
        x, y, width, height = (region[key] for key in ("x", "y", "width", "height"))
        draw.rectangle((x, y, x + width - 1, y + height - 1), fill=(0, 0, 0))
    return dict(masked_hash=_hash(masked.tobytes()), target=targets, options=options)


def check_reference_controls(items, directory):
    """Prove chance performance for any predictor deprived of reference pixels."""
    groups = defaultdict(list)
    errors = []
    for item in items:
        if item["family"] not in (*EXACT_MATCH_FAMILIES, "hue"):
            continue
        if not item["design"].get("optionSetId"):
            errors.append(f'{item["taskId"]}: missing reference-control set identity')
        with Image.open(Path(directory) / item["imageFilename"]) as source:
            image = source.convert("RGB")
        draw = ImageDraw.Draw(image)
        targets = [r for r in item["rendered"]["regions"] if r["role"] == "target"]
        if len(targets) != 1:
            errors.append(f'{item["taskId"]}: reference control requires exactly one target')
            continue
        r = targets[0]
        draw.rectangle((r["x"], r["y"], r["x"] + r["width"] - 1, r["y"] + r["height"] - 1), fill=(0, 0, 0))
        groups[(item["family"], item["prompt"], _hash(image.tobytes()))].append(item)
    for rows in groups.values():
        if sorted(row["groundTruth"]["choice"] for row in rows) != list("ABCD"):
            errors.append(f'{rows[0]["taskId"]}: identical reference-masked images must cover A/B/C/D exactly once')
        if len({row["design"].get("optionSetId") for row in rows}) != 1:
            errors.append(f'{rows[0]["taskId"]}: reference-control set identities disagree')
    return errors


def validate_dataset(manifest_path, *, require_complete=True):
    errors = []
    try:
        items = load_manifest(manifest_path)
    except (OSError, ValueError, TypeError, KeyError) as error:
        return dict(valid=False, task_count=0, errors=[str(error)])
    directory = Path(manifest_path).resolve().parent
    evidence, images, masks = {}, defaultdict(list), defaultdict(set)
    for item in items:
        try:
            evidence[item["taskId"]] = _item(item, directory)
            images[item["imageSha256"]].append(item)
            masks[(item["family"], item["design"].get("direction"), item["design"].get("layout"),
                   item["design"].get("condition"))].add(
                evidence[item["taskId"]]["masked_hash"])
        except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
            errors.append(f"{item['taskId']}: {error}")
    for copies in images.values():
        numeric_pair = (len({item["groupId"] for item in copies}) == 1
                        and all(item["family"] in NUMERIC_FAMILIES for item in copies)
                        and len({item["family"] for item in copies}) == len(copies))
        mapping_pair = (len(copies) == 2 and all(item["family"] == "samediff"
                        and item["design"].get("controlVersion") == CONTROL_VERSION for item in copies)
                        and len({item["groupId"] for item in copies}) == 1
                        and all(item["design"].get("mappingPairId") == item["groupId"] for item in copies)
                        and len({item["imageFilename"] for item in copies}) == 1
                        and {item["design"].get("direction") for item in copies} == {"sameA", "sameB"}
                        and {item["groundTruth"]["choice"] for item in copies} == {"A", "B"})
        if len(copies) > 1 and not (numeric_pair or mapping_pair):
            errors.append("Duplicate image outside an explicitly paired numeric-format or response-mapping group")
    if any(len(hashes) != 1 for hashes in masks.values()):
        errors.append("Pixels outside stimulus regions vary within a family and direction; possible answer leakage")
    controlled = any(row["design"].get("controlVersion") == CONTROL_VERSION for row in items)
    if require_complete or controlled:
        errors.extend(check_direct_controls(items, directory, require_complete=require_complete))
    if require_complete:
        counts = Counter(item["family"] for item in items)
        reference_crossed = any(row["design"].get("optionSetId") for row in items)
        expected_counts = COMPLETE_FAMILY_COUNTS
        if counts != Counter(expected_counts):
            errors.append(f"Release requires its frozen per-family task counts ({sum(expected_counts.values())} total)")
        if reference_crossed:
            errors.extend(check_reference_controls(items, directory))
        for family in CHOICE_FAMILIES:
            labels = choice_labels(family)
            expected = expected_counts[family] // len(labels)
            counts = Counter(item["groundTruth"]["choice"] for item in items if item["family"] == family)
            if counts != Counter({label: expected for label in labels}):
                errors.append(f"Correct option positions are not balanced for {family}")
        errors.extend(check_crossing(items))
        grouped = defaultdict(list)
        for item in items:
            grouped[item["groupId"]].append(item)
        for group, rows in grouped.items():
            families = {item["family"] for item in rows}
            if families & set(NUMERIC_FAMILIES):
                if (families != set(NUMERIC_FAMILIES) or len(rows) != 3
                        or len({item["imageSha256"] for item in rows}) != 1
                        or len({json.dumps(item["groundTruth"], sort_keys=True) for item in rows}) != 1):
                    errors.append(f"Numeric group {group} must share one target image across all three formats")
            if families & {"matching", "binding"}:
                if families != {"matching", "binding"} or len(rows) != 2:
                    errors.append(f"Matching/binding group {group} is incomplete")
                elif all(item["taskId"] in evidence for item in rows):
                    option_sets = [{label: (region["x"], region["y"], region["rgb"]) for label, region in evidence[item["taskId"]]["options"].items()} for item in rows]
                    if option_sets[0] != option_sets[1] or rows[0]["groundTruth"] != rows[1]["groundTruth"]:
                        errors.append(f"Matching/binding group {group} changes its option colors or positions")
    return dict(valid=not errors, task_count=len(items), family_counts=dict(Counter(item["family"] for item in items)), errors=errors)


def require_valid_dataset(manifest_path):
    report = validate_dataset(manifest_path)
    if not report["valid"]:
        raise ValueError("Dataset gate failed: " + "; ".join(report["errors"]))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest")
    args = parser.parse_args()
    report = validate_dataset(args.manifest)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["valid"] else 1)


if __name__ == "__main__":
    main()

"""Independently check decoded ColorBench stimuli before any paid request."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath

from PIL import Image, ImageDraw

from baseline.color_math import rgb_to_oklch
from baseline.evaluator import load_manifest
from baseline.protocol import CHOICE_FAMILIES, FAMILIES, NUMERIC_FAMILIES, choice_labels

FONT_SHA256 = "abdc775b21b1bc470d50c97e790d276f2054b7504e56e5bd3e64f48d68582322"
VIEWPORT = {"width": 800, "height": 640, "deviceScaleFactor": 1}


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
    _require(set(options) == (set(choice_labels(family)) if family in CHOICE_FAMILIES else set()), "Option count or labels disagree with family")
    _require(len(targets) == (0 if family in ("lightness", "chroma") else 1), "Unexpected target count")
    if family in NUMERIC_FAMILIES:
        _require(targets[0].get("rgb") == item["groundTruth"]["rgb"], "Numeric target differs from decoded pixels")
    elif family in ("matching", "binding", "gradient"):
        target = crops[("target", targets[0]["id"])]
        matches = [label for label in options if crops[("option", label)].size == target.size and crops[("option", label)].tobytes() == target.tobytes()]
        _require(matches == [item["groundTruth"]["choice"]], "Matching target must have exactly one correct option")
        _require(len({crops[("option", label)].tobytes() for label in options}) == len(options), "Distractor colors must remain distinct")
    else:
        _require(all("rgb" in region for region in options.values()), "Color-coordinate tasks require flat option colors")
        coordinates = {label: rgb_to_oklch(region["rgb"]) for label, region in options.items()}
        if family in ("lightness", "chroma"):
            dimension = "l" if family == "lightness" else "c"
            ordered = sorted(coordinates, key=lambda label: coordinates[label][dimension])
            _require(abs(coordinates[ordered[0]][dimension] - coordinates[ordered[-1]][dimension]) > .005, "Ordering gap vanished after rendering")
            high = item["design"].get("direction") in ("lighter", "more")
            answer = ordered[-1 if high else 0]
        else:
            target = rgb_to_oklch(targets[0]["rgb"])
            _require(target["c"] >= .02 and all(value["c"] >= .02 for value in coordinates.values()), "Hue target and options require chromatic colors")
            errors = {label: abs((value["h"] - target["h"] + 180) % 360 - 180) for label, value in coordinates.items()}
            ordered = sorted(errors, key=errors.get)
            _require(errors[ordered[0]] <= 3 and errors[ordered[1]] >= 35, "Hue reference is ambiguous after rendering")
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
            masks[(item["family"], item["design"].get("direction"))].add(evidence[item["taskId"]]["masked_hash"])
        except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
            errors.append(f"{item['taskId']}: {error}")
    for copies in images.values():
        if len(copies) > 1 and (len({item["groupId"] for item in copies}) != 1
                              or any(item["family"] not in NUMERIC_FAMILIES for item in copies)
                              or len({item["family"] for item in copies}) != len(copies)):
            errors.append("Duplicate image outside an explicitly paired numeric-format group")
    if any(len(hashes) != 1 for hashes in masks.values()):
        errors.append("Pixels outside stimulus regions vary within a family and direction; possible answer leakage")
    if require_complete:
        counts = Counter(item["family"] for item in items)
        if counts != Counter({family: 8 for family in FAMILIES}):
            errors.append("Pilot requires exactly eight tasks in each of nine families (72 total)")
        for family in CHOICE_FAMILIES:
            labels = choice_labels(family)
            counts = Counter(item["groundTruth"]["choice"] for item in items if item["family"] == family)
            if counts != Counter({label: 8 // len(labels) for label in labels}):
                errors.append(f"Correct option positions are not balanced for {family}")
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

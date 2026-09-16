"""Decoded-image invariants for the 0.4.0 direct-color experiment.

These bounds describe the finite input construction, not a model's strategy.
The single-patch oracle retains the whole image and prompt except one patch.
"""
from collections import Counter, defaultdict
import hashlib
from pathlib import Path

from PIL import Image, ImageDraw

from baseline.color_math import rgb_to_oklch
from baseline.protocol import get_prompt

CONTROL_VERSION = "0.4.0"
COMPLETE_COUNTS = {
    "matching": 48, "binding": 48, "lightness": 64, "chroma": 64,
    "hue": 32, "gradient": 16, "samediff": 48, "context": 80,
    "smallmatch": 64, "rgb": 16, "hsl": 16, "oklch": 16,
}
NEUTRAL = (238, 238, 238)
CONTEXT_CONDITIONS = {"neutral", "surround-0", "surround-1", "surround-2", "surround-3"}
SMALL_GEOMETRIES = {
    "filled-20": ("dot", 20, 0), "filled-84": ("dot", 84, 0),
    "outline-3": ("frame", 84, 3), "outline-12": ("frame", 84, 12),
}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _image(item, directory):
    with Image.open(Path(directory) / item["imageFilename"]) as source:
        return source.convert("RGB")


def _regions(item):
    return {(region["role"], region["id"]): region for region in item["rendered"]["regions"]}


def _box(region):
    x, y, width, height = (region[key] for key in ("x", "y", "width", "height"))
    return x, y, x + width, y + height


def _mask(image, box):
    x0, y0, x1, y1 = box
    ImageDraw.Draw(image).rectangle((x0, y0, x1 - 1, y1 - 1), fill=(0, 0, 0))


def _key(image, prompt):
    return prompt, hashlib.sha256(image.tobytes()).hexdigest()


def _groups(rows, field):
    groups = defaultdict(list)
    for row in rows:
        name = row["design"].get(field)
        _require(isinstance(name, str) and name, f"Missing {field}")
        groups[name].append(row)
    return groups


def _colors(row, image):
    return {key: image.getpixel((region["x"], region["y"])) for key, region in _regions(row).items()
            if key[0] in ("target", "option")}


def single_patch_ceiling(rows, directory, visible):
    """Bayes accuracy using all visible pixels except the other patch, plus prompt."""
    _require(visible in ("A", "B") and rows, "Single-patch control needs rows and A/B position")
    hidden = "B" if visible == "A" else "A"
    groups = defaultdict(Counter)
    for row in rows:
        image = _image(row, directory)
        _mask(image, _box(_regions(row)[("option", hidden)]))
        groups[_key(image, row["prompt"])][row["groundTruth"]["choice"]] += 1
    return sum(max(counts.values()) for counts in groups.values()) / len(rows)


def _pair_controls(rows, directory, complete):
    family = rows[0]["family"]
    equality = family == "samediff"
    field = "pairSetId" if equality else "comparisonSetId"
    groups = _groups(rows, field)
    if complete:
        _require(len(groups) == (6 if equality else 4), f"{family} has incomplete {field} coverage")
    directions = {"sameA", "sameB"} if equality else ({"lighter", "darker"} if family == "lightness" else {"more", "less"})
    for name, cell in groups.items():
        _require(len(cell) == (8 if equality else 16), f"{name}: incomplete pair crossing")
        _require({row["design"].get("direction") for row in cell} == directions, f"{name}: pair directions differ")
        if equality:
            for mapping, pair in _groups(cell, "mappingPairId").items():
                _require(len(pair) == 2 and {row["design"]["direction"] for row in pair} == directions,
                         f"{mapping}: incomplete response-mapping pair")
                _require(len({row["groupId"] for row in pair}) == 1
                         and all(row["groupId"] == mapping for row in pair)
                         and len({row["imageFilename"] for row in pair}) == 1
                         and len({row["imageSha256"] for row in pair}) == 1
                         and len({_image(row, directory).tobytes() for row in pair}) == 1,
                         f"{mapping}: response-mapping pair must share image and group")
        for direction in sorted(directions):
            selected = [row for row in cell if row["design"]["direction"] == direction]
            pairs = Counter()
            for row in selected:
                image = _image(row, directory)
                colors = _colors(row, image)
                a, b = colors[("option", "A")], colors[("option", "B")]
                pairs[(a, b)] += 1
                if equality:
                    same = a == b
                    same_choice = "A" if direction == "sameA" else "B"
                    wanted = same_choice if same else ("B" if same_choice == "A" else "A")
                    _require(row["design"].get("same") is same, f"{name}: decoded equality differs")
                else:
                    dimension = "l" if family == "lightness" else "c"
                    first, second = rgb_to_oklch(a)[dimension], rgb_to_oklch(b)[dimension]
                    _require(first != second, f"{name}: collapsed ordering pair")
                    high = direction in ("lighter", "more")
                    wanted = "A" if ((first > second) == high) else "B"
                _require(row["groundTruth"]["choice"] == wanted, f"{name}: decoded pair answer differs")
            palette = {color for pair in pairs for color in pair}
            _require(len(palette) == (2 if equality else 5), f"{name}: wrong number of decoded chain colors")
            if equality:
                expected = Counter((a, b) for a in palette for b in palette)
            else:
                ordered = sorted(palette, key=lambda color: rgb_to_oklch(color)[dimension])
                expected = Counter(pair for a, b in zip(ordered, ordered[1:]) for pair in ((a, b), (b, a)))
            _require(pairs == expected, f"{name}: decoded pairs do not form the prescribed crossing")
            ceiling = .5 if equality else .625
            for side in "AB":
                actual = single_patch_ceiling(selected, directory, side)
                _require(actual == ceiling, f"{name}/{direction}/{side}: single-patch ceiling {actual:g}, expected {ceiling:g}")


def _gradient_controls(rows, directory, complete):
    groups = _groups(rows, "optionSetId")
    if complete:
        _require(len(groups) == 4, "Gradient option-field coverage is incomplete")
    for name, cell in groups.items():
        _require(len(cell) == 4 and sorted(row["groundTruth"]["choice"] for row in cell) == list("ABCD"),
                 f"{name}: gradient reference crossing is incomplete")
        endpoints = set()
        fields = set()
        for row in cell:
            image = _image(row, directory)
            regions = _regions(row)
            target = regions[("target", "R")]
            crops = {label: image.crop(_box(regions[("option", label)])) for label in "ABCD"}
            reference = image.crop(_box(target))
            _require(all(crop.size == reference.size for crop in crops.values()), f"{name}: gradient dimensions differ")
            _require(len({crop.tobytes() for crop in crops.values()}) == 4, f"{name}: gradient interiors are not unique")
            matches = [label for label, crop in crops.items() if crop.tobytes() == reference.tobytes()]
            _require(matches == [row["groundTruth"]["choice"]], f"{name}: gradient full-field match differs")
            strips = [reference, *crops.values()]
            edge_signatures = {(strip.crop((0, 0, 1, strip.height)).tobytes(),
                                strip.crop((strip.width - 1, 0, strip.width, strip.height)).tobytes()) for strip in strips}
            _require(len(edge_signatures) == 1, f"{name}: gradient endpoints reveal the answer")
            for column in range(reference.width):
                signatures = Counter(crop.crop((column, 0, column + 1, crop.height)).tobytes()
                                     for crop in crops.values())
                _require(min(signatures.values()) >= 2,
                         f"{name}: gradient single-column signature identifies an option")
            histograms = [Counter({rgb: count for count, rgb in strip.getcolors(strip.width * strip.height)})
                          for strip in strips]
            _require(all(value == histograms[0] for value in histograms), f"{name}: gradient color histograms differ")
            if row["design"].get("grayscaleMatched") is True:
                _require(len({strip.convert("L").tobytes() for strip in strips}) == 1,
                         f"{name}: declared grayscale-matched gradients differ")
            _require(type(row["design"].get("grayscaleMatched")) is bool,
                     f"{name}: gradient must declare grayscaleMatched")
            x0, y0, x1, y1 = _box(target)
            _require(x1 - x0 > 2, f"{name}: gradient has no interior")
            _mask(image, (x0 + 1, y0, x1 - 1, y1))
            endpoints.add(_key(image, row["prompt"]))
            fields.add(tuple(crops[label].tobytes() for label in "ABCD"))
        _require(len(endpoints) == 1, f"{name}: endpoint-only image or prompt varies with answer")
        _require(len(fields) == 1, f"{name}: gradient option field changes with reference")
        _require(len({row["design"].get("grayscaleMatched") for row in cell}) == 1,
                 f"{name}: inconsistent grayscale declaration")
    if complete:
        _require(sum(cell[0]["design"]["grayscaleMatched"] for cell in groups.values()) == 2,
                 "Gradient controls require exactly two grayscale-matched fields")


def _intervention_controls(rows, directory, complete):
    family = rows[0]["family"]
    context = family == "context"
    conditions = CONTEXT_CONDITIONS if context else set(SMALL_GEOMETRIES)
    groups = _groups(rows, "interventionSetId")
    if complete:
        _require(len(groups) == 4, f"{family}: intervention palette coverage is incomplete")
    for name, palette in groups.items():
        _require(len(palette) == 4 * len(conditions), f"{name}: intervention crossing is incomplete")
        by_condition = _groups(palette, "condition")
        _require(set(by_condition) == conditions, f"{name}: intervention conditions differ")
        option_sets = []
        for condition, cell in by_condition.items():
            _require(len(cell) == 4 and sorted(row["groundTruth"]["choice"] for row in cell) == list("ABCD"),
                     f"{name}/{condition}: reference crossing is incomplete")
            option_ids = {row["design"].get("optionSetId") for row in cell}
            _require(len(option_ids) == 1 and all(isinstance(value, str) and value for value in option_ids),
                     f"{name}/{condition}: option field identity differs")
            option_sets.append(next(iter(option_ids)))
        _require(len(set(option_sets)) == len(conditions), f"{name}: conditions reuse an optionSetId")
        targets = defaultdict(list)
        for row in palette:
            targets[row["groupId"]].append(row)
        _require(len(targets) == 4, f"{name}: reference groups differ")
        surround_by_condition = {}
        for group, paired in targets.items():
            _require(len(paired) == len(conditions) and {row["design"].get("condition") for row in paired} == conditions,
                     f"{group}: matched intervention group is incomplete")
            signatures, outside, prompts, answers = set(), set(), set(), set()
            for row in paired:
                image = _image(row, directory)
                regions = _regions(row)
                _require(set(regions) == {("target", "R"), *(("option", label) for label in "ABCD")},
                         f"{group}: intervention regions differ")
                colors = _colors(row, image)
                signatures.add(tuple((key, colors[key], region["x"] * 2 + region["width"], region["y"] * 2 + region["height"])
                                     for key, region in sorted(regions.items())))
                prompts.add(row["prompt"])
                answers.add(row["groundTruth"]["choice"])
                condition = row["design"]["condition"]
                surrounds = {}
                for key, region in regions.items():
                    x0, y0, x1, y1 = _box(region)
                    crop = image.crop((x0, y0, x1, y1))
                    if context:
                        _require(crop.size == (84, 84) and crop.getextrema() == tuple((v, v) for v in colors[key]),
                                 f"{group}: context interior is not the matched flat 84px field")
                        if key[0] == "option":
                            color = image.getpixel((x0 - 1, y0 - 1))
                            surrounds[key[1]] = color
                            _require(list(color) == row["design"].get("surround", {}).get(key[1]),
                                     f"{group}: surround metadata differs from decoded pixels")
                            bounds = [(x0 - 12, y0 - 12, x1 + 12, y0), (x0 - 12, y1, x1 + 12, y1 + 12),
                                      (x0 - 12, y0, x0, y1), (x1, y0, x1 + 12, y1)]
                            for box in bounds:
                                ring = image.crop(box)
                                _require(ring.getextrema() == tuple((v, v) for v in color), f"{group}: surround ring is not uniform")
                                _mask(image, box)
                    else:
                        layout, size, stroke = SMALL_GEOMETRIES[condition]
                        _require((row["design"].get("layout"), row["design"].get("sizePx"), row["design"].get("strokePx")) == (layout, size, stroke),
                                 f"{group}: small-region geometry metadata differs")
                        _require(crop.size == (size, size), f"{group}: decoded small-region size differs")
                        expected = Image.new("RGB", (size, size), colors[key])
                        if stroke:
                            ImageDraw.Draw(expected).rectangle((stroke, stroke, size - stroke - 1, size - stroke - 1), fill=NEUTRAL)
                        _require(crop.tobytes() == expected.tobytes(), f"{group}: decoded fill or stroke differs")
                        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
                        full_box = image.crop((cx - 42, cy - 42, cx + 42, cy + 42))
                        expected_box = Image.new("RGB", (84, 84), NEUTRAL)
                        expected_box.paste(expected, ((84 - size) // 2, (84 - size) // 2))
                        _require(full_box.tobytes() == expected_box.tobytes(),
                                 f"{group}: decoded fill or stroke has uncontrolled surrounding pixels")
                        _mask(image, (cx - 42, cy - 42, cx + 42, cy + 42))
                outside.add(hashlib.sha256(image.tobytes()).hexdigest())
                if context:
                    ordered_surrounds = tuple(surrounds[label] for label in "ABCD")
                    previous = surround_by_condition.setdefault(condition, ordered_surrounds)
                    _require(previous == ordered_surrounds, f"{name}: surrounds change with reference")
            _require(len(signatures) == 1, f"{group}: matched colors or positions differ")
            _require(len(prompts) == 1 and len(answers) == 1, f"{group}: matched prompt or ground truth differs")
            _require(len(outside) == 1, f"{group}: pixels outside the intervention vary")
        if context:
            _require(surround_by_condition["neutral"] == (NEUTRAL,) * 4, f"{name}: neutral control is not neutral")
            base = surround_by_condition["surround-0"]
            _require(len(set(base)) == 4 and NEUTRAL not in base, f"{name}: surrounds must contain four distinct colors")
            for rotation in range(4):
                expected = tuple(base[(i + rotation) % 4] for i in range(4))
                _require(surround_by_condition[f"surround-{rotation}"] == expected, f"{name}: surround positions are not rotated")


def check_direct_controls(items, directory, *, require_complete=True):
    """Return violations of decoded experimental controls, without model calls."""
    errors = []
    if any(row["design"].get("controlVersion") != CONTROL_VERSION for row in items):
        errors.append("Every current task must declare controlVersion 0.4.0")
    if require_complete and Counter(row["family"] for row in items) != Counter(COMPLETE_COUNTS):
        errors.append("Direct-color controls require the complete 512-question cohort")
    for family in ("lightness", "chroma", "samediff", "gradient", "context", "smallmatch"):
        rows = [row for row in items if row["family"] == family]
        if not rows:
            continue
        try:
            for row in rows:
                _require(row["prompt"] == get_prompt(family, row["design"].get("direction")), f"{family}: canonical prompt differs")
            if family in ("lightness", "chroma", "samediff"):
                _pair_controls(rows, directory, require_complete)
            elif family == "gradient":
                _gradient_controls(rows, directory, require_complete)
            else:
                _intervention_controls(rows, directory, require_complete)
        except (OSError, KeyError, TypeError, ValueError, IndexError) as error:
            errors.append(f"{family}: {error}")
    return errors

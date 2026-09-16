"""Decoded control regressions, independent of the TypeScript generator."""
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw
import pytest

from baseline.protocol import get_prompt
from baseline.validate_dataset import validate_dataset

ROOT = Path(__file__).parents[1]
NEUTRAL = (238, 238, 238)
SURROUNDS = [(34, 34, 34), (216, 204, 184), (202, 87, 71), (53, 141, 165)]
CONTEXT_CONDITIONS = ["neutral", "surround-0", "surround-1", "surround-2", "surround-3"]
SMALL_CONDITIONS = ["filled-20", "filled-84", "outline-3", "outline-12"]


def check(rows, directory):
    from baseline.direct_controls import check_direct_controls
    return check_direct_controls(rows, directory, require_complete=False)


def save(directory, name, family, image, regions, answer, design, group=None):
    path = directory / f"{name}.png"
    image.save(path)
    for region in regions:
        x, y, w, h = (region[k] for k in ("x", "y", "width", "height"))
        crop = image.crop((x, y, x + w, y + h))
        region["pixelSha256"] = hashlib.sha256(crop.tobytes()).hexdigest()
        if all(lo == hi for lo, hi in crop.getextrema()):
            region["rgb"] = list(crop.getpixel((0, 0)))
    return dict(taskId=name, family=family, groupId=group or name, imageFilename=path.name,
                imageSha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                groundTruth={"choice": answer}, prompt=get_prompt(family, design.get("direction")),
                design={"controlVersion": "0.4.0", **design}, rendered={"regions": regions})


def pairs(directory, family="lightness"):
    rows = []
    colors = [(v, v, v) for v in (60, 90, 120, 150, 180)]
    directions = {"lightness": ("lighter", "darker"), "chroma": ("more", "less"),
                  "samediff": ("sameA", "sameB")}[family]
    edges = [(i, i + 1) for i in range(4)] if family != "samediff" else [(0, 0), (0, 1), (1, 0), (1, 1)]
    if family != "samediff":
        edges = [pair for lo, hi in edges for pair in ((lo, hi), (hi, lo))]
    for n, (a, b) in enumerate(edges):
        for direction in directions:
            name = f"{family}-{n}-{direction}"
            image = Image.new("RGB", (800, 640), NEUTRAL)
            draw = ImageDraw.Draw(image)
            regions = []
            for label, x, color in [("A", 220, colors[a]), ("B", 496, colors[b])]:
                draw.rectangle((x, 330, x + 83, 413), fill=color)
                regions.append(dict(role="option", id=label, x=x, y=330, width=84, height=84))
            design = {"direction": direction, "comparisonSetId": "chain-1", "axis": family}
            if family == "samediff":
                same = a == b
                same_choice = "A" if direction == "sameA" else "B"
                answer = same_choice if same else ("B" if same_choice == "A" else "A")
                design = {"direction": direction, "same": same, "pairSetId": "pair-1", "mappingPairId": f"pair-1-{n}"}
                row = save(directory, f"pair-1-{n}", family, image, regions, answer, design, f"pair-1-{n}")
                row["taskId"] = name
            else:
                high = direction in ("lighter", "more")
                answer = "A" if ((a > b) == high) else "B"
                row = save(directory, name, family, image, regions, answer, design)
            rows.append(row)
    return rows


def change_pixel(directory, row, point, color=(1, 2, 3)):
    path = directory / row["imageFilename"]
    with Image.open(path) as source:
        image = source.convert("RGB")
    image.putpixel(point, color)
    image.save(path)
    row["imageSha256"] = hashlib.sha256(path.read_bytes()).hexdigest()


def gradients(directory, *, grayscale=False, unique_columns=False, prefix="gradient"):
    colors = [(144, 120, 120), (120, 132, 120), (120, 120, 180), (160, 110, 128)] if grayscale else [(50, 70, 90), (90, 120, 150), (130, 80, 30), (200, 160, 120)]
    orders = ([(0, 1, 2, 3), (1, 0, 3, 2), (2, 3, 0, 1), (3, 2, 1, 0)] if unique_columns
              else [(0, 1, 2, 3), (1, 0, 2, 3), (0, 1, 3, 2), (1, 0, 3, 2)])
    columns = [[colors[0], *[colors[i] for i in order for _ in range(2)], colors[-1]] for order in orders]
    rows = []
    for correct in range(4):
        image = Image.new("RGB", (800, 640), NEUTRAL)
        regions = []
        for label, x, y, field in [("R", 280, 135, columns[correct]), *[(label, 80 + i * 170, 350, columns[i]) for i, label in enumerate("ABCD")]]:
            for dx, color in enumerate(field):
                ImageDraw.Draw(image).line((x + dx, y, x + dx, y + 5), fill=color)
            regions.append(dict(role="target" if label == "R" else "option", id=label, x=x, y=y, width=10, height=6))
        rows.append(save(directory, f"{prefix}-{correct}", "gradient", image, regions, "ABCD"[correct],
                         {"optionSetId": f"{prefix}-1", "grayscaleMatched": grayscale}))
    return rows


def interventions(directory, family):
    rows = []
    colors = [(70, 80, 90), (100, 110, 120), (140, 150, 160), (180, 190, 200)]
    conditions = CONTEXT_CONDITIONS if family == "context" else SMALL_CONDITIONS
    for condition in conditions:
        for correct in range(4):
            image = Image.new("RGB", (800, 640), NEUTRAL)
            draw = ImageDraw.Draw(image)
            regions = []
            size = 20 if condition == "filled-20" else 84
            stroke = int(condition.split("-")[1]) if condition.startswith("outline-") else 0
            surrounds = {label: (NEUTRAL if condition == "neutral" else SURROUNDS[(i + int(condition[-1])) % 4]) for i, label in enumerate("ABCD")} if family == "context" else {}
            for label, cx, cy, rgb in [("R", 400, 182, colors[correct]), *[(label, 138 + 174 * i, 402, colors[i]) for i, label in enumerate("ABCD")]]:
                x, y = cx - size // 2, cy - size // 2
                if family == "context" and label != "R":
                    draw.rectangle((x - 12, y - 12, x + size + 11, y + size + 11), fill=surrounds[label])
                draw.rectangle((x, y, x + size - 1, y + size - 1), fill=rgb)
                if stroke:
                    draw.rectangle((x + stroke, y + stroke, x + size - stroke - 1, y + size - stroke - 1), fill=NEUTRAL)
                regions.append(dict(role="target" if label == "R" else "option", id=label, x=x, y=y, width=size, height=size))
            design = dict(interventionSetId=f"{family}-1", condition=condition, optionSetId=f"{family}-1-{condition}", axis="lightness")
            if family == "context":
                design["surround"] = {k: list(v) for k, v in surrounds.items()}
            else:
                design.update(layout="frame" if stroke else "dot", sizePx=size, strokePx=stroke)
            rows.append(save(directory, f"{family}-{condition}-{correct}", family, image, regions, "ABCD"[correct], design, f"{family}-1-reference-{'ABCD'[correct]}"))
    return rows


def test_old_gradient_shortcut_cannot_be_marked_as_current_controlled_dataset(tmp_path):
    source = ROOT / "dataset/colorbench-v0.3.2"
    rows = [r for r in json.loads((source / "manifest.json").read_text()) if r["family"] == "gradient"]
    shutil.copytree(source / "fonts", tmp_path / "fonts")
    for row in rows:
        row["design"]["controlVersion"] = "0.4.0"
        shutil.copyfile(source / row["imageFilename"], tmp_path / row["imageFilename"])
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(rows))
    report = validate_dataset(path, require_complete=False)
    assert not report["valid"], "Old endpoint-only gradients were admitted as new controlled inputs"
    assert any("endpoint" in error.lower() for error in report["errors"])


@pytest.mark.parametrize("family,ceiling", [("lightness", .625), ("samediff", .5)])
def test_whole_image_single_patch_bound_and_forged_nuisance_rejection(tmp_path, family, ceiling):
    from baseline.direct_controls import single_patch_ceiling
    rows = pairs(tmp_path, family)
    assert check(rows, tmp_path) == []
    for side in "AB":
        for direction in {r["design"]["direction"] for r in rows}:
            selected = [r for r in rows if r["design"]["direction"] == direction]
            assert single_patch_ceiling(selected, tmp_path, side) == ceiling
    change_pixel(tmp_path, rows[0], (30, 30))
    for row in rows:
        if row["imageFilename"] == rows[0]["imageFilename"]:
            row["imageSha256"] = rows[0]["imageSha256"]
    assert any("single-patch" in error for error in check(rows, tmp_path))


@pytest.mark.parametrize("mutation", ["prompt", "missing", "label", "mapping-image"])
def test_equality_crossing_rejects_prompt_answer_coverage_and_mapping_drift(tmp_path, mutation):
    rows = pairs(tmp_path, "samediff")
    assert check(rows, tmp_path) == []
    if mutation == "prompt": rows[0]["prompt"] += " The answer is A."
    elif mutation == "missing": rows.pop()
    elif mutation == "label": rows[0]["groundTruth"]["choice"] = "B"
    else:
        old = rows[0]["imageFilename"]
        shutil.copyfile(tmp_path / old, tmp_path / "changed.png")
        rows[0]["imageFilename"] = "changed.png"
        change_pixel(tmp_path, rows[0], (20, 20))
    assert check(rows, tmp_path)


@pytest.mark.parametrize("mutation", ["endpoint", "histogram", "duplicate", "prompt", "grayscale"])
def test_gradient_interior_controls_reject_each_shortcut_and_mislabel(tmp_path, mutation):
    rows = gradients(tmp_path, grayscale=True)
    assert check(rows, tmp_path) == []
    if mutation == "prompt": rows[0]["prompt"] += " Answer A."
    else:
        row = rows[0]
        option = next(r for r in row["rendered"]["regions"] if r["id"] == "B")
        point = (option["x"] + (0 if mutation == "endpoint" else 3), option["y"])
        if mutation == "duplicate":
            path = tmp_path / row["imageFilename"]
            with Image.open(path) as source: image = source.convert("RGB")
            a = next(r for r in row["rendered"]["regions"] if r["id"] == "A")
            image.paste(image.crop((a["x"], a["y"], a["x"] + a["width"], a["y"] + a["height"])), (option["x"], option["y"]))
            image.save(path)
        else: change_pixel(tmp_path, row, point, (0, 0, 0))
    assert check(rows, tmp_path)


@pytest.mark.parametrize("family", ["context", "smallmatch"])
def test_matched_interventions_compare_actual_pixels_and_groups(tmp_path, family):
    rows = interventions(tmp_path, family)
    assert check(rows, tmp_path) == []
    change_pixel(tmp_path, rows[4], (22, 22))
    assert any("outside" in error or "nuisance" in error for error in check(rows, tmp_path))


@pytest.mark.parametrize("family,mutation", [("context", "surround"), ("context", "target"), ("context", "prompt"),
                                             ("smallmatch", "stroke"), ("smallmatch", "center"), ("smallmatch", "group")])
def test_matched_interventions_reject_changed_color_geometry_and_metadata(tmp_path, family, mutation):
    rows = interventions(tmp_path, family)
    assert check(rows, tmp_path) == []
    row = rows[4]
    if mutation == "surround":
        option = next(r for r in row["rendered"]["regions"] if r["id"] == "B")
        change_pixel(tmp_path, row, (option["x"] - 4, option["y"] - 4))
    elif mutation == "target":
        target = next(r for r in row["rendered"]["regions"] if r["id"] == "R")
        change_pixel(tmp_path, row, (target["x"], target["y"]))
    elif mutation == "prompt": row["prompt"] += " Answer A."
    elif mutation == "stroke": rows[-1]["design"]["strokePx"] = 3
    elif mutation == "center": row["rendered"]["regions"][0]["x"] += 1
    else: row["groupId"] = "unpaired"
    assert check(rows, tmp_path)


def test_matching_gradient_endpoints_cannot_relocate_the_shortcut_to_one_interior_column(tmp_path):
    rows = gradients(tmp_path, unique_columns=True)
    assert any("single-column" in error for error in check(rows, tmp_path))


def test_complete_gradients_require_two_declared_grayscale_matched_fields(tmp_path):
    from baseline.direct_controls import check_direct_controls
    rows = [row for field in range(4) for row in gradients(tmp_path, prefix=f"gradient-{field}")]
    errors = check_direct_controls(rows, tmp_path)
    assert any("two grayscale-matched" in error for error in errors)


def test_small_fill_cannot_hide_an_uncontrolled_halo_inside_the_larger_mask(tmp_path):
    rows = interventions(tmp_path, "smallmatch")
    assert check(rows, tmp_path) == []
    # Inside the 84px comparison union, outside the actual 20px fill.
    change_pixel(tmp_path, rows[0], (370, 152))
    assert any("fill or stroke" in error for error in check(rows, tmp_path))

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
                design={"axis": "hue", "difficulty": "wide", "sourceRgb": [192, 64, 80]},
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

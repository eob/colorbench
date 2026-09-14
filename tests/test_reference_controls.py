"""The decoded control includes the whole image outside R and the full prompt."""
import copy
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw
import pytest

from baseline.validate_dataset import check_reference_controls


@pytest.fixture
def controlled_images(tmp_path):
    colors = [(40, 60, 80), (80, 100, 120), (120, 140, 160), (160, 180, 200)]
    rows = []
    for position, color in enumerate(colors):
        image = Image.new("RGB", (80, 80), (238, 238, 238))
        draw = ImageDraw.Draw(image)
        draw.rectangle((30, 10, 39, 19), fill=color)
        for option, rgb in enumerate(colors):
            draw.rectangle((option * 20, 40, option * 20 + 9, 49), fill=rgb)
        name = f"sample-{position}.png"
        image.save(tmp_path / name)
        rows.append(dict(taskId=f"sample-{position}", family="matching", imageFilename=name,
                         prompt="Match R", groundTruth={"choice": "ABCD"[position]},
                         design={"optionSetId": "sample"},
                         rendered={"regions": [dict(role="target", x=30, y=10, width=10, height=10)]}))
    return rows, tmp_path


def test_identical_reference_masked_fields_cover_all_answers(controlled_images):
    rows, directory = controlled_images
    assert check_reference_controls(rows, directory) == []


@pytest.mark.parametrize("mutation", ["label", "prompt", "answer", "identity", "drop"])
def test_control_rejects_any_visible_or_mapping_shortcut(controlled_images, mutation):
    rows, directory = controlled_images
    if mutation == "label":
        path = directory / rows[0]["imageFilename"]
        with Image.open(path) as source:
            image = source.copy()
        image.putpixel((0, 0), (0, 0, 0))
        image.save(path)
    elif mutation == "prompt":
        rows[0]["prompt"] += " Hint: A"
    elif mutation == "answer":
        rows[0]["groundTruth"]["choice"] = "B"
    elif mutation == "identity":
        rows[0]["design"].pop("optionSetId")
    else:
        rows.pop()
    assert check_reference_controls(rows, directory)

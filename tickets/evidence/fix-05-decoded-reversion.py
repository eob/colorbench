"""Reproduce causal regression checks without modifying the shared working tree."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
BASE = "edfeef9cf7f41860615075cee6a4b1fc63b89cda"


def run(directory, expression, expected_failures):
    command = [sys.executable, "-m", "pytest", "tests/test_direct_controls.py",
               "tests/test_dataset_gate.py", "-q", "-k", expression]
    print("COMMAND:", " ".join(command), flush=True)
    result = subprocess.run(command, cwd=directory, capture_output=True, text=True)
    print(result.stdout, end="", flush=True)
    print(result.stderr, end="", flush=True)
    assert result.returncode == 1, f"Expected causal regression, got exit {result.returncode}"
    assert f"{expected_failures} failed," in result.stdout


with tempfile.TemporaryDirectory(prefix="colorbench-decoded-reversion-") as temporary:
    directory = Path(temporary)
    shutil.copytree(ROOT / "baseline", directory / "baseline", ignore=shutil.ignore_patterns("__pycache__"))
    (directory / "tests").mkdir()
    for name in ("test_direct_controls.py", "test_dataset_gate.py"):
        shutil.copyfile(ROOT / "tests" / name, directory / "tests" / name)
    shutil.copytree(ROOT / "src/assets", directory / "src/assets")
    shutil.copytree(ROOT / "dataset/colorbench-v0.3.2", directory / "dataset/colorbench-v0.3.2")
    validator = directory / "baseline/validate_dataset.py"
    current_validator = validator.read_text()
    historical = subprocess.run(["git", "show", f"{BASE}:baseline/validate_dataset.py"],
                                cwd=ROOT, check=True, capture_output=True, text=True).stdout
    validator.write_text(historical)
    print("CONTROL A: restore the pre-fix decoded validator only.", flush=True)
    run(directory, "old_gradient_shortcut or duplicate_images_only_allow", 4)
    validator.write_text(current_validator)

    controls = directory / "baseline/direct_controls.py"
    implementation = controls.read_text()
    blocks = [
        '''            for column in range(reference.width):
                signatures = Counter(crop.crop((column, 0, column + 1, crop.height)).tobytes()
                                     for crop in crops.values())
                _require(min(signatures.values()) >= 2,
                         f"{name}: gradient single-column signature identifies an option")
''',
        '''    if complete:
        _require(sum(cell[0]["design"]["grayscaleMatched"] for cell in groups.values()) == 2,
                 "Gradient controls require exactly two grayscale-matched fields")
''',
        '''                        full_box = image.crop((cx - 42, cy - 42, cx + 42, cy + 42))
                        expected_box = Image.new("RGB", (84, 84), NEUTRAL)
                        expected_box.paste(expected, ((84 - size) // 2, (84 - size) // 2))
                        _require(full_box.tobytes() == expected_box.tobytes(),
                                 f"{group}: decoded fill or stroke has uncontrolled surrounding pixels")
''',
    ]
    for block in blocks:
        assert implementation.count(block) == 1
        implementation = implementation.replace(block, "")
    controls.write_text(implementation)
    print("CONTROL B: remove only the three review-driven strengthening checks.", flush=True)
    run(directory, "relocate_the_shortcut or two_declared_grayscale or uncontrolled_halo", 3)
    print("Both isolated reversions reproduced their expected failures; shared source was unchanged.", flush=True)

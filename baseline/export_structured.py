"""Export compact publication data only from an independently verified sealed run."""
import argparse
import hashlib
from pathlib import Path

from baseline.finalize import verify_finalization
from baseline.runner import write_json


def build_structured_benchmark(run_dir: str | Path, *, root=None) -> dict:
    directory = Path(run_dir)
    report = verify_finalization(directory, root=root)
    return {**{key: value for key, value in report.items() if key != 'results'},
            'source_run_path': directory.resolve().relative_to(Path(root).resolve() if root else Path(__file__).resolve().parents[1]).as_posix(),
            'final_results_sha256': hashlib.sha256((directory / 'final_results.json').read_bytes()).hexdigest(),
            'finalization_sha256': hashlib.sha256((directory / 'finalization.json').read_bytes()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    write_json(Path(args.output), build_structured_benchmark(args.run_dir))


if __name__ == '__main__':
    main()

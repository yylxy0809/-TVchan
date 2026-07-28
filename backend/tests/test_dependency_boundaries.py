import subprocess
import sys
from pathlib import Path


def test_dependency_boundaries() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_dependency_boundaries.py"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr

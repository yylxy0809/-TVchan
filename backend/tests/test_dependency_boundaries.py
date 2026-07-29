"""Counterexamples proving the dependency-boundary gate can reject violations."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Protocol, cast

import pytest


class Gate(Protocol):
    PACKAGE: str

    def check_package(self, package_root: Path) -> tuple[list[object], dict[str, int]]: ...


REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = REPO_ROOT / "scripts" / "check_dependency_boundaries.py"
_spec = importlib.util.spec_from_file_location("dependency_boundary_gate", GATE_PATH)
assert _spec and _spec.loader
module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = module
_spec.loader.exec_module(module)
gate = cast(Gate, module)

DECLARED_LAYERS = ("domain", "application", "infrastructure", "adapters", "bootstrap")


def _scaffold(tmp_path: Path, files: dict[str, str] | None = None) -> Path:
    package_root = tmp_path / "backend" / "src" / gate.PACKAGE
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text('"""Package."""\n', encoding="utf-8")
    for layer in DECLARED_LAYERS:
        directory = package_root / layer
        directory.mkdir()
        (directory / "__init__.py").write_text('"""Layer."""\n', encoding="utf-8")
    ports = package_root / "application" / "ports"
    ports.mkdir()
    (ports / "__init__.py").write_text('"""Ports."""\n', encoding="utf-8")
    for relative, source in (files or {}).items():
        target = package_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
    return package_root


def _details(package_root: Path) -> list[str]:
    violations, _ = gate.check_package(package_root)
    return [str(violation) for violation in violations]


def _cli_details(package_root: Path) -> tuple[int, str]:
    scripts = package_root.parents[2] / "scripts"
    scripts.mkdir(exist_ok=True)
    shutil.copy2(GATE_PATH, scripts / GATE_PATH.name)
    result = subprocess.run(
        [sys.executable, str(scripts / GATE_PATH.name)],
        cwd=package_root.parents[2],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stdout + result.stderr


def test_real_repository_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_dependency_boundaries.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "modules inspected" in result.stdout


def test_clean_scaffold_passes(tmp_path: Path) -> None:
    assert _details(_scaffold(tmp_path)) == []


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("from tvchan.adapters import http\n", "first-party 'tvchan.adapters'"),
        ("from ...adapters import http\n", "first-party 'tvchan.adapters'"),
        ("from ...adapters.http import router\n", "first-party 'tvchan.adapters.http'"),
        ("from ... import adapters\n", "first-party 'tvchan.adapters'"),
    ],
)
def test_domain_cross_layer_imports_are_rejected(
    tmp_path: Path, source: str, expected: str
) -> None:
    path = "domain/deep/rule.py" if source.startswith("from ...") else "domain/rule.py"
    assert any(expected in detail for detail in _details(_scaffold(tmp_path, {path: source})))


def test_application_direct_implementation_import_is_rejected(tmp_path: Path) -> None:
    details = _details(
        _scaffold(tmp_path, {"application/use_case.py": "import tvchan.adapters.api\n"})
    )
    assert any("first-party 'tvchan.adapters.api'" in detail for detail in details)


def test_restricted_layer_third_party_import_is_rejected(tmp_path: Path) -> None:
    details = _details(_scaffold(tmp_path, {"domain/rule.py": "import requests\n"}))
    assert any("third-party 'requests'" in detail for detail in details)


def test_similar_unknown_namespace_is_not_a_first_party_violation(tmp_path: Path) -> None:
    package_root = _scaffold(
        tmp_path,
        {"domain/rule.py": "import tvchan.applications_helper\nimport tvchan.infrastructurex\n"},
    )
    assert _details(package_root) == []


def test_unknown_on_disk_layer_is_rejected(tmp_path: Path) -> None:
    details = _details(_scaffold(tmp_path, {"infrastructurex/module.py": "pass\n"}))
    assert any("infrastructurex" in detail and "unregistered layer" in detail for detail in details)


def test_relative_import_escaping_package_is_rejected(tmp_path: Path) -> None:
    details = _details(_scaffold(tmp_path, {"domain/rule.py": "from ...... import something\n"}))
    assert any("escapes package" in detail for detail in details)


@pytest.mark.parametrize(
    "source",
    [
        "import importlib\nimportlib.import_module('tvchan.adapters.api')\n",
        "__import__('tvchan.adapters.api')\n",
    ],
)
def test_literal_dynamic_import_is_rejected_in_restricted_layer(
    tmp_path: Path, source: str
) -> None:
    details = _details(_scaffold(tmp_path, {"domain/rule.py": source}))
    assert any("unsupported dynamic import 'tvchan.adapters.api'" in detail for detail in details)


def test_literal_dynamic_import_is_rejected_in_application(tmp_path: Path) -> None:
    details = _details(_scaffold(tmp_path, {"application/use_case.py": "__import__('requests')\n"}))
    assert any("unsupported dynamic import 'requests'" in detail for detail in details)


def test_dynamic_literal_import_is_reported_by_cli(tmp_path: Path) -> None:
    package_root = _scaffold(
        tmp_path,
        {"domain/rule.py": "import importlib\nimportlib.import_module('requests')\n"},
    )
    exit_code, output = _cli_details(package_root)
    assert exit_code == 1
    assert "domain/rule.py:2: unsupported dynamic import 'requests'" in output


def test_syntax_error_is_reported_as_a_violation(tmp_path: Path) -> None:
    details = _details(_scaffold(tmp_path, {"domain/broken.py": "def broken(:\n"}))
    assert any("cannot be parsed, so it was never checked" in detail for detail in details)


def test_syntax_error_is_reported_by_cli(tmp_path: Path) -> None:
    package_root = _scaffold(tmp_path, {"domain/broken.py": "def broken(:\n"})
    exit_code, output = _cli_details(package_root)
    assert exit_code == 1
    assert "domain/broken.py: cannot be parsed, so it was never checked" in output

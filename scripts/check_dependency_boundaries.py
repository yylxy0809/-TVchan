"""Fail when a Wave 0 layer imports a forbidden higher-level layer."""

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "backend" / "src" / "tvchan"
FORBIDDEN_PREFIXES: dict[str, tuple[str, ...]] = {
    "domain": (
        "tvchan.application",
        "tvchan.infrastructure",
        "tvchan.adapters",
        "tvchan.bootstrap",
        "fastapi",
    ),
    "application": ("tvchan.infrastructure", "tvchan.adapters", "tvchan.bootstrap", "fastapi"),
    "infrastructure": ("tvchan.adapters", "tvchan.bootstrap", "fastapi"),
    "adapters": ("tvchan.bootstrap", "fastapi"),
}


def imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def main() -> int:
    violations: list[str] = []
    for layer, forbidden in FORBIDDEN_PREFIXES.items():
        for path in (PACKAGE_ROOT / layer).rglob("*.py"):
            for module in imported_modules(path):
                if module.startswith(forbidden):
                    relative_path = path.relative_to(PACKAGE_ROOT)
                    violations.append(f"{relative_path} imports forbidden {module}")

    if violations:
        print("Dependency boundary violations:", *violations, sep="\n")
        return 1

    print("Dependency boundaries: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

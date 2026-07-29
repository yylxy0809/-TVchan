"""Enforce TVchan's frozen layered dependency contract."""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "backend" / "src" / "tvchan"
PACKAGE = "tvchan"
ROOT_LAYER = "<package root>"
IGNORED_DIRECTORIES = frozenset({"__pycache__"})


@dataclass(frozen=True)
class LayerPolicy:
    allowed_first_party: tuple[str, ...]
    allow_third_party: bool
    denied_third_party: tuple[str, ...] = ()


LAYER_POLICIES: dict[str, LayerPolicy] = {
    ROOT_LAYER: LayerPolicy((), False),
    "domain": LayerPolicy(("tvchan.domain",), False),
    "application": LayerPolicy(("tvchan.domain", "tvchan.application"), False),
    "infrastructure": LayerPolicy(
        ("tvchan.domain", "tvchan.application.ports", "tvchan.infrastructure"),
        True,
        ("fastapi",),
    ),
    "adapters": LayerPolicy(
        ("tvchan.domain", "tvchan.application.ports", "tvchan.adapters"),
        True,
        ("fastapi",),
    ),
    "bootstrap": LayerPolicy((PACKAGE,), True),
}
REGISTERED_PREFIXES = tuple(f"{PACKAGE}.{layer}" for layer in LAYER_POLICIES if layer != ROOT_LAYER)


@dataclass(frozen=True)
class Violation:
    location: str
    detail: str

    def __str__(self) -> str:
        return f"{self.location}: {self.detail}"


@dataclass(frozen=True)
class ModuleReference:
    module: str
    lineno: int
    is_base: bool


def _is_within(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(f"{prefix}.")


def _package_for(path: Path, package_root: Path) -> str:
    relative = path.relative_to(package_root)
    return ".".join((PACKAGE, *relative.parts[:-1]))


def _layer_for(path: Path, package_root: Path) -> str:
    parts = path.relative_to(package_root).parts
    return ROOT_LAYER if len(parts) == 1 else parts[0]


def _resolve_relative(level: int, module: str | None, package: str) -> str | None:
    parts = package.split(".")
    if level > len(parts):
        return None
    parent = ".".join(parts[: len(parts) - (level - 1)])
    return f"{parent}.{module}" if module else parent


def _is_literal_dynamic_import(node: ast.Call) -> bool:
    if (
        not node.args
        or not isinstance(node.args[0], ast.Constant)
        or not isinstance(node.args[0].value, str)
    ):
        return False
    if isinstance(node.func, ast.Name):
        return node.func.id == "__import__"
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "import_module"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "importlib"
    )


def module_references(
    source: str, package: str, location: str, restricted_layer: bool
) -> tuple[list[ModuleReference], list[Violation]]:
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [], [Violation(location, f"cannot be parsed, so it was never checked ({error})")]

    references: list[ModuleReference] = []
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            references.extend(
                ModuleReference(alias.name, node.lineno, True) for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                target = _resolve_relative(node.level, node.module, package)
                if target is None:
                    dots = "." * node.level
                    violations.append(
                        Violation(
                            f"{location}:{node.lineno}",
                            f"relative import '{dots}{node.module or ''}' escapes package "
                            f"'{package}'",
                        )
                    )
                    continue
            elif node.module:
                target = node.module
            else:
                continue
            references.append(ModuleReference(target, node.lineno, True))
            references.extend(
                ModuleReference(f"{target}.{alias.name}", node.lineno, False)
                for alias in node.names
                if alias.name != "*"
            )
        elif restricted_layer and isinstance(node, ast.Call) and _is_literal_dynamic_import(node):
            first_argument = node.args[0]
            assert isinstance(first_argument, ast.Constant)
            assert isinstance(first_argument.value, str)
            violations.append(
                Violation(
                    f"{location}:{node.lineno}",
                    f"unsupported dynamic import '{first_argument.value}' in a restricted layer",
                )
            )
    return references, violations


def _classify(reference: ModuleReference, layer: str, policy: LayerPolicy) -> str | None:
    module = reference.module
    is_registered = module == PACKAGE or any(
        _is_within(module, prefix) for prefix in REGISTERED_PREFIXES
    )
    if is_registered:
        if module == PACKAGE or any(
            _is_within(module, prefix) for prefix in policy.allowed_first_party
        ):
            return None
        return f"layer '{layer}' must not import first-party '{module}'"

    # Only the five registered layer prefixes carry first-party dependency semantics. A similarly
    # named, unknown tvchan namespace cannot be a valid on-disk layer: structural validation below
    # rejects it if it is introduced into this repository.
    if _is_within(module, PACKAGE):
        return None

    root = module.split(".")[0]
    if root in sys.stdlib_module_names or not reference.is_base:
        return None
    if not policy.allow_third_party:
        return (
            f"layer '{layer}' must not import third-party '{root}'; external capability is "
            "reached through Ports"
        )
    if any(_is_within(root, denied) for denied in policy.denied_third_party):
        return f"layer '{layer}' must not import third-party '{root}'"
    return None


def _structural_violations(package_root: Path) -> list[Violation]:
    if not package_root.is_dir():
        return [
            Violation(str(package_root), "package root is missing, so nothing could be checked")
        ]
    try:
        discovered = {
            entry.name
            for entry in package_root.iterdir()
            if entry.is_dir() and entry.name not in IGNORED_DIRECTORIES
        }
    except OSError as error:
        return [
            Violation(
                str(package_root), f"could not be listed, so nothing could be checked ({error})"
            )
        ]

    violations = [
        Violation(
            f"{package_root.name}/{name}",
            "is an unregistered layer; declare its policy in LAYER_POLICIES before use",
        )
        for name in sorted(discovered - LAYER_POLICIES.keys())
    ]
    violations.extend(
        Violation(
            f"{package_root.name}/{layer}",
            "is declared in LAYER_POLICIES but absent from disk; the layer was never scanned",
        )
        for layer in sorted(set(LAYER_POLICIES) - {ROOT_LAYER} - discovered)
    )
    return violations


def _python_files(package_root: Path) -> list[Path]:
    return sorted(
        path
        for path in package_root.rglob("*.py")
        if not IGNORED_DIRECTORIES.intersection(path.relative_to(package_root).parts)
    )


def check_package(package_root: Path) -> tuple[list[Violation], dict[str, int]]:
    violations = _structural_violations(package_root)
    scanned: dict[str, int] = {}
    if not package_root.is_dir():
        return violations, scanned
    try:
        paths = _python_files(package_root)
    except OSError as error:
        violations.append(Violation(str(package_root), f"could not be scanned ({error})"))
        return violations, scanned

    for path in paths:
        layer = _layer_for(path, package_root)
        policy = LAYER_POLICIES.get(layer)
        if policy is None:
            continue
        location = path.relative_to(package_root).as_posix()
        scanned[layer] = scanned.get(layer, 0) + 1
        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            violations.append(
                Violation(location, f"could not be read, so it was never checked ({error})")
            )
            continue
        references, problems = module_references(
            source, _package_for(path, package_root), location, layer in {"domain", "application"}
        )
        violations.extend(problems)
        reported: set[str] = set()
        for reference in references:
            detail = _classify(reference, layer, policy)
            if detail and detail not in reported:
                reported.add(detail)
                violations.append(Violation(f"{location}:{reference.lineno}", detail))

    for layer in sorted(LAYER_POLICIES):
        if layer not in scanned and not any(
            v.location == f"{package_root.name}/{layer}" for v in violations
        ):
            violations.append(
                Violation(
                    f"{package_root.name}/{layer}",
                    "contains no Python module, so the layer contributed no evidence",
                )
            )
    return violations, scanned


def main() -> int:
    violations, scanned = check_package(PACKAGE_ROOT)
    if violations:
        print(
            "Dependency boundary violations:",
            *(f"  {violation}" for violation in violations),
            sep="\n",
        )
        return 1
    inspected = ", ".join(f"{layer}={count}" for layer, count in sorted(scanned.items()))
    print(f"Dependency boundaries: OK ({sum(scanned.values())} modules inspected; {inspected})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Tests for the version consistency check (scripts/check_versions.py)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "check_versions", Path(__file__).resolve().parent.parent / "scripts" / "check_versions.py"
)
assert _SPEC is not None
assert _SPEC.loader is not None
check_versions = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(check_versions)


def _write_project(root: Path, **overrides: str) -> None:
    versions = {
        "manifest": "1.6.0",
        "package": "1.6.0",
        "lock": "1.6.0",
        "lock_root": "1.6.0",
        "pyproject": "1.6.0",
        "changelog": "1.6.0",
    } | overrides
    (root / "custom_components" / "zte_h186").mkdir(parents=True)
    (root / "custom_components" / "zte_h186" / "manifest.json").write_text(
        json.dumps({"version": versions["manifest"]}), encoding="utf-8"
    )
    (root / "package.json").write_text(json.dumps({"version": versions["package"]}))
    (root / "package-lock.json").write_text(
        json.dumps(
            {"version": versions["lock"], "packages": {"": {"version": versions["lock_root"]}}}
        )
    )
    (root / "pyproject.toml").write_text(f'[project]\nversion = "{versions["pyproject"]}"\n')
    (root / "CHANGELOG.md").write_text(
        f"# Changelog\n\n## [Unreleased]\n\n## [{versions['changelog']}] - 2026-11-21\n\n"
        "## [1.5.1] - 2026-11-20\n"
    )


def test_repository_versions_agree() -> None:
    """The real repository passes the check."""
    assert check_versions.main() == 0


def test_agreeing_versions_pass(tmp_path: Path) -> None:
    _write_project(tmp_path)
    assert check_versions.main(tmp_path) == 0


@pytest.mark.parametrize(
    "place", ["manifest", "package", "lock", "lock_root", "pyproject", "changelog"]
)
def test_any_differing_place_fails(tmp_path: Path, place: str) -> None:
    _write_project(tmp_path, **{place: "1.5.1"})
    assert check_versions.main(tmp_path) == 1

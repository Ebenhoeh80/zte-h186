"""Check that every place that carries the version of the integration says the same.

The version lives in ``manifest.json`` (what Home Assistant and HACS read), ``package.json`` and
``package-lock.json`` (two places), ``pyproject.toml`` and the newest entry of ``CHANGELOG.md``.
Run it from anywhere: ``python scripts/check_versions.py``. Exit code 1 if they differ.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tomllib

ROOT = Path(__file__).resolve().parent.parent
_HEADING = re.compile(r"^##\s+\[(?P<version>[^\]]+)\]", re.MULTILINE)


def _changelog_version(text: str) -> str:
    """Return the newest released version of the changelog (``[Unreleased]`` is skipped)."""
    for match in _HEADING.finditer(text):
        if match["version"].strip().lower() != "unreleased":
            return match["version"].strip()
    raise ValueError("CHANGELOG.md has no version heading")


def collect_versions(root: Path) -> dict[str, str]:
    """Return the version found in each place, by the name of the place."""
    lock = json.loads((root / "package-lock.json").read_text(encoding="utf-8"))
    return {
        "manifest.json": json.loads(
            (root / "custom_components" / "zte_h186" / "manifest.json").read_text(encoding="utf-8")
        )["version"],
        "package.json": json.loads((root / "package.json").read_text(encoding="utf-8"))["version"],
        "package-lock.json (top)": lock["version"],
        "package-lock.json (packages)": lock["packages"][""]["version"],
        "pyproject.toml": tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))[
            "project"
        ]["version"],
        "CHANGELOG.md": _changelog_version((root / "CHANGELOG.md").read_text(encoding="utf-8")),
    }


def main(root: Path = ROOT) -> int:
    """Print the versions and return 1 if they are not all the same."""
    versions = collect_versions(root)
    for place, version in versions.items():
        print(f"{place:32} {version}")
    if len(set(versions.values())) != 1:
        print("\nThe versions differ. Bring all of them to the same version.", file=sys.stderr)
        return 1
    print("\nAll versions agree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Consistency checks for the files a release touches outside the Python code."""

from __future__ import annotations

import json
import re

from scripts.check_versions import ROOT, collect_versions

_OLD_ZIP = re.compile(r"zte-h186-v\d+\.\d+\.\d+\.zip")


def _asset_name() -> str:
    return json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))["filename"]


def _text(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_readmes_name_the_actual_release_asset() -> None:
    asset = _asset_name()
    for name in ("README.md", "README.de.md"):
        text = _text(name)
        assert f"`{asset}`" in text, f"{name} does not name the released asset"
        assert _OLD_ZIP.search(text) is None, f"{name} still advertises an old archive"


def test_release_zip_helper_uses_the_actual_asset_name() -> None:
    text = _text("create_release_zip.py")
    assert f'"{_asset_name()}"' in text
    assert _OLD_ZIP.search(text) is None


def test_security_policy_covers_the_current_release() -> None:
    minor = ".".join(collect_versions(ROOT)["manifest.json"].split(".")[:2]) + ".x"
    supported = re.findall(r"^\| (\d+\.\d+\.x)\s+\| :white_check_mark:", _text("SECURITY.md"), re.M)
    assert supported == [minor]


def test_release_checklist_covers_every_version_source() -> None:
    checklist = _text("RELEASING.md")
    for source in collect_versions(ROOT):
        assert source.split(" (")[0] in checklist, f"RELEASING.md omits {source}"
    assert "[Unreleased]" in _text("CHANGELOG.md")


_ROADMAP = re.compile(r"^## 🗺️.*?$(.*?)(^---|\Z)", re.MULTILINE | re.DOTALL)


def _roadmap_items(name: str) -> list[str]:
    match = _ROADMAP.search(_text(name))
    assert match is not None, f"{name} has no roadmap section"
    return [line for line in match.group(1).splitlines() if line.startswith(("- 💡", "- 🔜"))]


def test_all_readmes_have_the_same_roadmap() -> None:
    english = _roadmap_items("README.md")
    assert len(english) == 1
    for name in ("README.de.md", "README.fr.md", "README.es.md"):
        assert len(_roadmap_items(name)) == len(english), f"{name} has a stale roadmap"

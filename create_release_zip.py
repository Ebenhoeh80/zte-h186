#!/usr/bin/env python3
"""Package the ZTE H186 integration into a release ZIP archive."""

import os
from pathlib import Path
import zipfile

def create_zip():
    base_dir = Path(__file__).resolve().parent
    public_dir = base_dir / "public"
    public_dir.mkdir(exist_ok=True)
    zip_path = public_dir / "zte-h186-v1.0.0.zip"

    files_to_include = [
        "icon.png",
        "hacs.json",
        "README.md",
        "CONTRIBUTING.md",
        "CHANGELOG.md",
        "LICENSE",
        "requirements.txt",
        ".gitignore",
        "zte_h186.stats.sh",
        "zte_h186_stats.py",
    ]

    dirs_to_include = [
        "custom_components/zte_h186",
        "images",
        ".github",
    ]

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name in files_to_include:
            file_path = base_dir / file_name
            if file_path.is_file():
                zip_file.write(file_path, arcname=file_name)

        for dir_name in dirs_to_include:
            dir_path = base_dir / dir_name
            if dir_path.is_dir():
                for root, _, files in os.walk(dir_path):
                    for file in files:
                        full_path = Path(root) / file
                        rel_path = full_path.relative_to(base_dir)
                        zip_file.write(full_path, arcname=str(rel_path))

    print(f"Created release zip: {zip_path} ({zip_path.stat().st_size} bytes)")

if __name__ == "__main__":
    create_zip()

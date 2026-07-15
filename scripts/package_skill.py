#!/usr/bin/env python3
"""Package a skill folder into an uploadable .skill file.

Usage:
    python3 scripts/package_skill.py skills/<skill-name> [output-dir]

A .skill file is a zip archive of the skill folder. The default output
directory is dist/.
"""

import fnmatch
import re
import sys
import zipfile
from pathlib import Path

EXCLUDE_DIRS = {"__pycache__", "node_modules", "evals"}
EXCLUDE_FILES = {".DS_Store"}
EXCLUDE_GLOBS = {"*.pyc"}


def validate(skill_path: Path) -> bool:
    skill_md = skill_path / "SKILL.md"
    if not skill_md.is_file():
        print(f"ERROR: {skill_md} not found")
        return False
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        print("ERROR: SKILL.md is missing YAML frontmatter (--- ... ---)")
        return False
    front = match.group(1)
    for field in ("name", "description"):
        if not re.search(rf"^{field}\s*:", front, re.MULTILINE):
            print(f"ERROR: frontmatter is missing required field '{field}'")
            return False
    return True


def excluded(rel: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return True
    if rel.name in EXCLUDE_FILES:
        return True
    return any(fnmatch.fnmatch(rel.name, pat) for pat in EXCLUDE_GLOBS)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    skill_path = Path(sys.argv[1]).resolve()
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("dist")
    if not skill_path.is_dir():
        print(f"ERROR: {skill_path} is not a directory")
        return 1
    if not validate(skill_path):
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{skill_path.name}.skill"
    with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(skill_path.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(skill_path)
            if excluded(rel):
                continue
            zf.write(path, Path(skill_path.name) / rel)
            print(f"  + {skill_path.name}/{rel}")
    print(f"\nPackaged: {out_file}")
    print("Upload it at claude.ai -> Settings -> Capabilities -> Skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())

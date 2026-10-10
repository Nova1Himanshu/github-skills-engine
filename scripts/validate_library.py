#!/usr/bin/env python3
"""Validate configuration and curated SKILL.md frontmatter before ingestion."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "sources.json"
CURATED = ROOT / "library" / "curated"


def main() -> int:
    errors = []
    try:
        config = json.loads(CONFIG.read_text(encoding="utf-8"))
        if not isinstance(config.get("repositories"), list):
            errors.append("config/sources.json: 'repositories' must be a list")
        for index, item in enumerate(config.get("repositories", [])):
            if not isinstance(item, dict) or not item.get("repo"):
                errors.append(f"config/sources.json: repository item {index} is missing 'repo'")
    except Exception as exc:
        errors.append(f"config/sources.json: invalid JSON ({exc})")

    skills = sorted(CURATED.rglob("SKILL.md")) if CURATED.exists() else []
    if not skills:
        errors.append("No curated SKILL.md files found.")
    for path in skills:
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            errors.append(f"{path.relative_to(ROOT)}: missing YAML frontmatter opening")
            continue
        end = text.find("\n---\n", 4)
        if end == -1:
            errors.append(f"{path.relative_to(ROOT)}: missing YAML frontmatter closing")
            continue
        front = text[4:end]
        if not re.search(r"(?m)^name:\s*\S+", front):
            errors.append(f"{path.relative_to(ROOT)}: missing 'name'")
        if not re.search(r"(?m)^description:\s*.+", front):
            errors.append(f"{path.relative_to(ROOT)}: missing 'description'")

    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Validation passed: {len(skills)} curated skills and source config.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Check sync metadata and saved text; never execute imported content."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def validate(root: Path) -> None:
    config = json.loads((root / "config/sources.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "library/manifest.json").read_text(encoding="utf-8"))
    report = (root / "reports/latest-report.md").read_text(encoding="utf-8")
    if re.search(r"(?m)^- (?:ERROR\b|WARNING: the GitHub tree response was truncated\.)", report):
        raise ValueError("Sync report contains an error or a truncated tree")

    expected = Counter((str(s["repo"]).strip(), str(s.get("ref", "HEAD")).strip())
                       for s in config["repositories"] if s.get("enabled", True))
    sources = manifest["sources"]
    files = manifest["files"]
    actual = Counter((s["repo"], s["ref"]) for s in sources)
    if actual != expected or any(n != 1 for n in actual.values()):
        raise ValueError("Manifest sources do not match enabled repositories")

    sections = []
    current = None
    for line in report.splitlines():
        if line.startswith("## "):
            current = {"repo": line[3:], "entries": []}
            sections.append(current)
        elif current is not None:
            if line.startswith("- Ref: "):
                current["ref"] = line[7:]
            elif line.startswith("- Selected Markdown files: "):
                current["selected"] = int(line.rsplit(" ", 1)[1])
            elif line.startswith(("- Imported skill:", "- Draft reference:")):
                match = re.fullmatch(r"- (Imported skill|Draft reference): `([^`]+)`  `([^`]+)`", line)
                if not match:
                    raise ValueError("Malformed report file entry")
                label, path, output = match.groups()
                current["entries"].append((path, output, "skill" if label == "Imported skill" else "draft-reference"))
    if Counter((s["repo"], s["ref"]) for s in sections) != expected:
        raise ValueError("Report sources do not match enabled repositories")

    identities = Counter((f["repo"], f["ref"], f["path"]) for f in files)
    outputs = Counter(f["output_path"] for f in files)
    if any(n != 1 for n in identities.values()) or any(n != 1 for n in outputs.values()):
        raise ValueError("Duplicate manifest identity or output path")
    if any((f["repo"], f["ref"]) not in actual for f in files):
        raise ValueError("Manifest file belongs to an unknown source")
    for source, section in zip(sorted(sources, key=lambda s: (s["repo"], s["ref"])),
                               sorted(sections, key=lambda s: (s["repo"], s["ref"]))):
        selected = [f for f in files if (f["repo"], f["ref"]) == (source["repo"], source["ref"])]
        if source["selected_files"] != len(selected) or section["selected"] != len(selected):
            raise ValueError("Selected count does not match completed downloads")
        if Counter(section["entries"]) != Counter((f["path"], f["output_path"], f["kind"]) for f in selected):
            raise ValueError("Report file entries do not match manifest")
    for entry in files:
        relative = Path(entry["output_path"])
        allowed = "imported" if entry["kind"] == "skill" else "drafts" if entry["kind"] == "draft-reference" else None
        if relative.is_absolute() or allowed is None or relative.parts[:2] != ("library", allowed):
            raise ValueError("Invalid manifest output path or kind")
        path = (root / relative).resolve()
        if not path.is_relative_to((root / "library" / allowed).resolve()):
            raise ValueError("Manifest output escapes its destination")
        if not path.is_file() or path.stat().st_size != entry["bytes_saved"]:
            raise ValueError(f"Missing or incomplete saved file: {relative}")


def main() -> int:
    try:
        validate(ROOT)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print(f"Post-sync validation failed: {exc}", file=sys.stderr)
        return 1
    print("Post-sync validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

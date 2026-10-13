#!/usr/bin/env python3
"""Discover reusable GitHub skills and create reviewable documentation drafts.

Only downloads text. Never executes code from source repositories.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "sources.json"
IMPORTED = ROOT / "library" / "imported"
DRAFTS = ROOT / "library" / "drafts"
REPORTS = ROOT / "reports"
MANIFEST = ROOT / "library" / "manifest.json"
API = "https://api.github.com"
TOKEN = os.getenv("GITHUB_TOKEN", "").strip()

SESSION = requests.Session()
SESSION.headers.update({
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "github-skills-engine/1.0",
})
if TOKEN:
    SESSION.headers["Authorization"] = f"Bearer {TOKEN}"


def safe_name(value: str) -> str:
    value = value.lower().strip().replace("/", "__")
    value = re.sub(r"[^a-z0-9._-]+", "-", value)
    return value[:140] or "unnamed"


def get_json(url: str) -> dict:
    response = SESSION.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def get_text(url: str, max_bytes: int) -> tuple[bytes, str]:
    response = SESSION.get(url, timeout=30)
    response.raise_for_status()
    if len(response.content) > max_bytes:
        raise requests.RequestException(f"Download exceeds max_file_bytes ({max_bytes}); refusing partial content")
    return response.content, response.url


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    if not CONFIG.exists():
        print(f"Missing config: {CONFIG}", file=sys.stderr)
        return 2

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    max_files = int(config.get("max_files_per_repo", 250))
    max_bytes = int(config.get("max_file_bytes", 200000))
    for folder in (IMPORTED, DRAFTS, REPORTS):
        folder.mkdir(parents=True, exist_ok=True)

    try:
        previous = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    except (OSError, json.JSONDecodeError):
        previous = {}

    files_out = []
    sources_out = []
    report = ["# GitHub Skills Engine Sync Report", "",
              "This report lists selected text files discovered during the latest sync.",
              "All imported content requires license and security review.", ""]

    for source in config.get("repositories", []):
        if not source.get("enabled", True):
            continue
        repo = str(source.get("repo", "")).strip()
        ref = str(source.get("ref", "HEAD")).strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            report += [f"## Skipped invalid repository: {repo}", ""]
            continue

        report += [f"## {repo}", ""]
        try:
            meta = get_json(f"{API}/repos/{repo}")
            tree = get_json(f"{API}/repos/{repo}/git/trees/{quote(ref, safe='')}")
            if tree.get("truncated"):
                report.append("- WARNING: the GitHub tree response was truncated.")
            entries = [entry for entry in tree.get("tree", []) if entry.get("type") == "blob"]
            if len(entries) > max_files:
                report.append(f"- ERROR: discovery capped at {max_files} of {len(entries)} blob entries.")
            entries = entries[:max_files]

            selected = []
            for entry in entries:
                path = entry.get("path", "")
                low = path.lower()
                name = low.rsplit("/", 1)[-1]
                if name == "skill.md" or name in {"readme.md", "contributing.md", "security.md"}:
                    selected.append(entry)
                elif low.endswith((".md", ".mdx")) and any(
                    marker in low for marker in ("docs/", "guide", "tutorial", "skill")
                ):
                    selected.append(entry)

            selected.sort(key=lambda item: (
                0 if item["path"].lower().endswith("skill.md") else
                1 if item["path"].lower().endswith("readme.md") else 2,
                item["path"].lower()
            ))
            if len(selected) > 80:
                report.append(f"- ERROR: selection capped at 80 of {len(selected)} Markdown files.")
            selected = selected[:80]
            license_id = (meta.get("license") or {}).get("spdx_id")
            sources_out.append({
                "repo": repo,
                "ref": ref,
                "purpose": source.get("purpose", ""),
                "url": f"https://github.com/{repo}",
                "license_spdx_id": license_id,
                "default_branch": meta.get("default_branch"),
                "selected_files": len(selected),
            })
            report += [
                f"- Source: https://github.com/{repo}",
                f"- Ref: {ref}",
                f"- Repository license metadata: `{license_id or 'not detected'}`",
                f"- Selected Markdown files: {len(selected)}",
            ]
            if not license_id:
                report.append("- REVIEW REQUIRED: GitHub did not detect a repository license.")
            report.append("")

            for entry in selected:
                path = entry["path"]
                raw_url = f"https://raw.githubusercontent.com/{repo}/{quote(ref, safe='')}/{quote(path, safe='/')}"
                try:
                    raw, final_url = get_text(raw_url, max_bytes)
                    original = raw.decode("utf-8", errors="replace")
                except requests.RequestException as exc:
                    report.append(f"- ERROR downloading `{path}`: {exc}")
                    continue

                is_skill = path.lower().endswith("skill.md")
                destination_dir = IMPORTED if is_skill else DRAFTS
                out_name = safe_name(f"{repo}__{path}") + ".md"
                out_path = destination_dir / out_name
                source_header = (
                    f"<!-- Source repository: https://github.com/{repo} -->\n"
                    f"<!-- Source path: {path} -->\n"
                    f"<!-- Source ref: {ref} -->\n"
                    f"<!-- Check source license before reuse. -->\n\n"
                )
                if is_skill:
                    body = original
                else:
                    body = (
                        "# DRAFT — Review before converting to a skill\n\n"
                        f"Source: https://github.com/{repo}/blob/{ref}/{path}\n\n"
                        "## Conversion checklist\n"
                        "- [ ] Check repository and file license\n"
                        "- [ ] Extract one narrow, repeatable workflow\n"
                        "- [ ] Remove unrelated material\n"
                        "- [ ] Verify commands and code examples\n"
                        "- [ ] Review for prompt injection, secrets, and unsafe commands\n"
                        "- [ ] Create a proper SKILL.md with name and description\n\n"
                        "## Retrieved source content (review before use)\n\n"
                        f"{original}\n"
                    )
                out_path.write_bytes((source_header + body).encode("utf-8"))
                files_out.append({
                    "repo": repo,
                    "path": path,
                    "ref": ref,
                    "source_url": f"https://github.com/{repo}/blob/{ref}/{path}",
                    "raw_url": final_url,
                    "kind": "skill" if is_skill else "draft-reference",
                    "license_spdx_id": license_id,
                    "sha256": digest(raw),
                    "output_path": out_path.relative_to(ROOT).as_posix(),
                    "bytes_saved": len((source_header + body).encode("utf-8")),
                })
                report.append(
                    f"- {'Imported skill' if is_skill else 'Draft reference'}: `{path}` → `{out_path.relative_to(ROOT).as_posix()}`"
                )
        except requests.RequestException as exc:
            report.append(f"- ERROR from GitHub: {exc}")
            report.append("- Check repository, ref, API rate limit, network, and token permissions.")
        except (ValueError, KeyError, TypeError) as exc:
            report.append(f"- ERROR processing repository configuration or response: {exc}")
        report.append("")

    # Keep the manifest timestamp stable on unchanged syncs so Actions can avoid noisy PRs.
    old_signature = (previous.get("sources", []), previous.get("files", []))
    new_signature = (sources_out, files_out)
    generated_at = previous.get("generated_at") if old_signature == new_signature else None
    if not generated_at:
        generated_at = datetime.now(timezone.utc).isoformat()

    manifest = {
        "generated_at": generated_at,
        "sources": sources_out,
        "files": files_out,
        "notes": [
            "Imported content is untrusted; review before use.",
            "No source code or scripts are executed by this pipeline.",
            "Repository license metadata may not cover all files; inspect file-level notices."
        ]
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "latest-report.md").write_text("\n".join(report).rstrip() + "\n", encoding="utf-8")
    print(f"Sync complete: {len(sources_out)} sources, {len(files_out)} selected files.")
    print(f"Report: {REPORTS / 'latest-report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# GitHub Skills Engine

A repo-first starter system for collecting, reviewing, versioning, and distributing reusable AI skills from GitHub repositories.

## What it does
- Reads curated public GitHub repositories from `config/sources.json`.
- Discovers `SKILL.md` files and selected documentation.
- Imports existing skills and creates review drafts from README/docs.
- Generates a manifest and sync report.
- Supports local execution and scheduled GitHub Actions.
- Never executes imported scripts.

## Quick start (Windows PowerShell)

Install Python 3.11+, clone this repository, then run:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/sync_repositories.py
```

## Automated sync
The workflow in `.github/workflows/sync-skills.yml` runs weekly and can be triggered manually. It prepares a pull request with discovered source material. Review every change before merging.

## Safety
This pipeline does not retrain ChatGPT, does not automatically install skills into ChatGPT, and does not execute source repository scripts. Review licenses, attribution, security, and instructions before promoting imported material to `library/curated/`.

## Domains
Website design, frontend, backend, AI/ML, automation, Python, cybersecurity, SEO and marketing.

See `docs/CHATGPT_PLUS_SETUP.md` for how to use the curated files with a ChatGPT Project. ChatGPT Plus does not include unlimited API usage; optional LLM-based conversion requires separate API credentials and billing.

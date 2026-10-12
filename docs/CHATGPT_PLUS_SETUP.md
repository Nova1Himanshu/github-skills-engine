# Using this library with ChatGPT Plus

## Recommended path
Use a ChatGPT Project as your workspace for planning, testing, and applying selected skills.

1. Create a Project named `AI Skills Lab`, if Projects are available.
2. Add the content of `docs/PROJECT_INSTRUCTIONS.txt` to its project instructions.
3. Upload selected reviewed skills from `library/curated/` as reference files.
4. Keep this GitHub repository as the source of truth.
5. When a skill changes, review the diff and upload the approved version again if you need it available as Project knowledge.

If GitHub is available in ChatGPT's Apps/Connectors settings, connect only the repositories you need. Do not assume the connector auto-installs or continuously syncs all skills.

## Limits
- ChatGPT Plus does not run this repository's scheduled pipeline; GitHub Actions does.
- This repo does not automatically install files into ChatGPT.
- Custom GPT creation availability can change by account and plan; do not depend on it.
- The manual prompt-packet workflow does not use the OpenAI API and requires no API credits. Any separate API integrations you add later would use separate billing.

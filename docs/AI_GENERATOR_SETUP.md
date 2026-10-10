# AI skill generation setup

This optional workflow converts source documentation drafts into AI-generated `SKILL.md` candidates.

## Before the first run

1. Merge the source-discovery PR so source drafts and `library/manifest.json` exist on `main`.
2. Create an API key in the OpenAI API platform. API billing is separate from ChatGPT Plus; see https://help.openai.com/en/articles/9039756-managing-billing-settings-on-the-chatgpt-web-and-api-platform.
3. Set a budget/usage limit in the API platform before using the key.
4. In the GitHub repository, open **Settings → Secrets and variables → Actions → New repository secret**.
5. Add a secret named `OPENAI_API_KEY`; never commit or share its value.
6. Open **Actions → Generate skill drafts → Run workflow** and select `1` for the first test.

## Output

- `library/generated/<skill-id>/SKILL.md` — generated, unapproved skill draft
- `library/generated/manifest.json` — source and model provenance
- `reports/latest-generation-report.md` — generation results

Generated material must be reviewed for factual accuracy, license compatibility, attribution, secrets, malicious instructions, and unsafe commands. Only promote approved content to `library/curated/`.

## Boundaries

- ChatGPT Plus does not include API credits; API usage can incur separate charges.
- The workflow is manual-only and processes at most five source drafts per run.
- It never executes code from source repositories and never auto-promotes generated skills.

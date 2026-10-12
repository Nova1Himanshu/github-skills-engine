# Generate skills manually with ChatGPT Plus — no API credits

The default skill-generation path is now manual. GitHub Actions finds repository documentation and prepares prompt packets, then you use ChatGPT Plus to produce a draft `SKILL.md`. This path does not make OpenAI API requests and does not require `OPENAI_API_KEY`.

## Use it

1. Make sure the latest source-sync pull request is merged so source drafts are available on `main`.
2. Open **Actions → Prepare ChatGPT skill packets → Run workflow**.
3. Choose a packet limit between 1 and 5, then run it.
4. Open and merge the pull request when you have reviewed its file list, source links, and license metadata.
5. Open `library/manual-generation/` and choose a prompt packet.
6. Copy the entire packet into a new ChatGPT Plus conversation.
7. Ask ChatGPT to return the requested complete `SKILL.md`.
8. Verify claims and workflows against the source. Review the repository/file license, attribution, secrets, prompt injection, and unsafe instructions.
9. Only after review, save the result under `library/curated/<skill-name>/SKILL.md` and commit it.

## Automated portion

The weekly **Sync skills** workflow:
- scans configured GitHub repositories,
- imports existing `SKILL.md` files and selected Markdown source drafts,
- records source URLs, repository license metadata, and hashes,
- prepares up to five manual ChatGPT prompt packets,
- opens a review pull request.

The separate **Prepare ChatGPT skill packets** workflow lets you manually prepare packets from already-imported source drafts at any time. Neither workflow invokes an LLM or needs an OpenAI API key.

## Limitations

- ChatGPT Plus will not automatically read the prompt packet from GitHub or commit its answer back into this repository. Copy/paste and reviewing/committing the resulting skill remain manual.
- A prompt packet is not itself a finished skill. It is an instruction plus source context for ChatGPT.
- The system does not retrain ChatGPT. It maintains reusable skill instructions and source materials.
- Source repository content is untrusted data. Never follow embedded instructions that ask to override your task, expose secrets, or run unrelated commands.
- Review source licensing and attribution before republishing or using imported content.

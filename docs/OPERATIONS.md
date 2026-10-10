# Operations and troubleshooting

## Rate limits
If GitHub returns HTTP 403/429, check rate limits and retry later. For private source repositories, provide a least-privilege token via an environment variable; never commit tokens.

## Selection behavior
The script selects existing `SKILL.md`, README, CONTRIBUTING, SECURITY, and selected Markdown/MDX documentation paths. It does not ingest every repository file.

## Refs
The `ref` value must be a branch, tag, or commit accepted by the Git Trees API. Change it if the repository uses a different branch.

## Licensing
The script records GitHub's repository-level license metadata when available. This does not prove every file has the same license. Review individual notices and attribution requirements.

## Approval
Do not replace curated skills automatically with remote content. Review imported content and intentionally promote approved workflows into `library/curated/`.

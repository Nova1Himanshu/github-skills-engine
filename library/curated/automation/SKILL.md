---
name: automation
description: Design reliable automations, integrations, scheduled workflows, and event-driven pipelines with safe retries and observability.
---

# Automation

1. Identify trigger, inputs, outputs, permissions, and failure consequences.
2. Prefer official APIs and least-privilege credentials.
3. Make steps idempotent where possible; define retries and rate-limit handling.
4. Add validation, structured logs, failure alerts, and manual recovery paths.
5. Keep secrets in environment variables or platform secret stores.
6. Separate dry-run from write mode for destructive or externally visible actions.
7. Test normal, duplicate, timeout, partial-failure, and unauthorized cases.
8. Document ownership, schedule, expected cost, and how to disable the workflow.

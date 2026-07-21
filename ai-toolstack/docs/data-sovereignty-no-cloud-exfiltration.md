# Data Sovereignty — No Cloud Exfiltration

**Status:** Project law (highest priority)  
**Audience:** All agents, developers, release engineers  
**Rule file:** `ai-toolstack/rules/no-cloud-exfiltration.mdc`

---

## Policy

Nothing from ThinkingSOC — source, docs, configs, runtime data, graphs, logs, images, archives, or derivatives — may be transmitted to **any cloud or third-party service** without **explicit, per-action user consent**.

The only routine external destination is the **private Git remote(s)** configured in this repository, and uploads there happen **only** when the user runs them manually or explicitly instructs an agent in that session.

## Prohibited (non-exhaustive)

- Public or private cloud storage (S3, GCS, Azure Blob, etc.)
- Paste services, public gists, anonymous file hosts
- Sending repo context to external LLM APIs unless user explicitly opts in for that call
- CI artifacts to public buckets; telemetry that includes code or paths
- Shipping container/image layers containing unreleased proprietary bits to public registries without approval

## Required in new work

When adding documentation, scripts, CI, or agent tooling:

1. Assume **local-first / private-only** data paths.
2. Do not add default cloud upload, sync, or phone-home behavior.
3. Document any network egress in the design; default is **none**.

## Agent rule

Cursor agents: see `no-cloud-exfiltration.mdc` (`alwaysApply: true`).

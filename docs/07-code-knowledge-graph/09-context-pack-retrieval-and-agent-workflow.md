# 09 - Context Pack Retrieval And Agent Workflow

## Purpose

This document defines how AgentCore agents should use code metadata before reading source code.

## Context Pack

A Context Pack is a compact, structured bundle created from code metadata. It gives an agent enough information to decide where to work, what to inspect, what risks exist, and whether source code must be read.

A context pack should include:

- task summary and retrieval reason.
- selected files and symbols.
- signatures and source spans.
- responsibility and behavior summaries.
- dependency and call graph highlights.
- related tests.
- related docs, decisions, and rules.
- risk tags.
- freshness and confidence.
- source-read recommendations.
- token estimate.
- evidence references.

## Retrieval Algorithm

```text
build_context_pack(task):
    query = normalize_task(task)
    candidates = search_metadata(query)
    graph_expansion = expand_related_symbols(candidates)
    ranked = rank_by_relevance_freshness_confidence_risk(candidates + graph_expansion)
    selected = fit_metadata_budget(ranked)
    escalations = evaluate_source_read_policy(selected, task)
    return ContextPack(selected, escalations, evidence)
```

## Agent Decision Flow

1. Read Common Context and project profile.
2. Request a metadata context pack.
3. Inspect metadata summaries, signatures, dependencies, tests, and risk tags.
4. Decide whether the task can be planned from metadata.
5. Read targeted source slices only when escalation policy requires it.
6. Produce plan, patch, documentation, review, or tests with evidence references.
7. Record which metadata records and source slices were used.
8. Feed outcome quality back into metadata effectiveness scoring.

## Use Cases

### Initial Code Generation

The agent uses metadata to locate relevant symbols, understand APIs, find tests, and avoid reading unrelated files. Source is read only for target files and dependencies that are actually modified.

### Bug Reduction

Metadata surfaces risk tags, known side effects, call relationships, related tests, and stale documentation. This helps the agent avoid changing a function without understanding its callers and test coverage.

### Architecture Quality

Metadata exposes module ownership, dependency direction, forbidden imports, service boundaries, and coupling. The agent can detect architectural drift before writing code.

### Reduced Rework

When repeated failures happen around the same symbol or dependency, metadata can link issues, decisions, tests, and common context. Future agents start with better context instead of rediscovering the same facts.

### Token Consumption

The system can measure source bytes avoided, metadata tokens used, source tokens used after escalation, and final success. This allows reporting the difference between metadata-first and source-first workflows.

### Code Review

Review agents can start from metadata diffs: changed symbols, impacted callers, risk tags, test coverage, and dependency changes. They read source only for risky or ambiguous areas.

### Documentation Generation

Documentation agents can use metadata to generate or update docs for changed symbols only. They should read source when metadata confidence is low or behavior summaries are stale.

### Test Planning

Test agents can map changed symbols to existing tests, missing tests, fixture requirements, and live-test candidates.

## Metrics

AgentCore should report:

- percentage of tasks completed with metadata-first planning.
- number of avoided full-file reads.
- token savings compared with source-first retrieval.
- source escalation rate by task type.
- metadata stale rate.
- confidence distribution by language and repository.
- bug rate for metadata-first tasks vs source-first tasks.
- architecture violation detection rate.
- time to locate relevant code.

## Safety Rule

Metadata-first does not mean metadata-only. For code modification, security-sensitive behavior, persistence, migrations, auth, deployment, or low-confidence records, the agent must read targeted source before making changes.

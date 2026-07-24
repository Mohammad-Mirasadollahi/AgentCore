---
doc_id: ac.doc.ops.risk-register-and-open-decisions
title: Risk Register and Open Decisions
doc_type: gap
status: draft
schema_version: '1.0'
owner: platform-docs
summary: This document captures important risks and unresolved decisions that should be tracked
  before implementation.
tags:
- gap
- ops
phase: 09-platform-governance-operations
canonical_path: docs/09-platform-governance-operations/07-risk-register-and-open-decisions.md
lifecycle_lane: future
concern_lane: gap
audience_lane:
- platform-engineering
- agents
authority: informative
visibility: internal
linked_symbols: []
doc_version: 1.0.0
updated_at: '2026-07-24'
---

# Risk Register and Open Decisions

## Purpose

This document captures important risks and unresolved decisions that should be tracked before implementation. It prevents hidden assumptions from becoming architectural debt.

## Risk Register

### Risk 1 - Context Pollution

Agents may receive stale, irrelevant, or conflicting memory.

Mitigation: current-state resolution, WeightProfiles, deprecation, conflict detection, and source references.

### Risk 2 - Over-Automation

Agents may perform risky changes without enough human oversight.

Mitigation: rule engine, escalation, capability profiles, and fail-closed policies.

### Risk 3 - Documentation Fatigue

Too many low-value drift findings may cause teams to ignore documentation signals.

Mitigation: severity thresholds, doc flags, waiver policy, and owner-based routing.

### Risk 4 - Model Cost Growth

LLM calls may become expensive if every event triggers model reasoning.

Mitigation: deterministic checks, hash diffing, prompt caching, local models, and tiered model routing.

### Risk 5 - Vendor Lock-In

The platform may become dependent on one IDE, model, or agent provider.

Mitigation: Universal Agent JSON, adapter contracts, capability profiles, and model routing abstraction.

### Risk 6 - Graph Inaccuracy

Dynamic languages or incomplete parsing may create wrong call relationships.

Mitigation: confidence scores, verification, exact/probable/ambiguous resolution states, and review Tasks.

### Risk 7 - Port Conflicts in Development

Local development may fail when services use common default ports.

Mitigation: project-scoped non-default port profiles, startup preflight checks, and overrideable configuration.

### Risk 8 - Sensitive Data Leakage into Prompts

Logs, diffs, or artifacts may include secrets or customer data.

Mitigation: redaction pipeline, sensitivity labels, prompt safety checks, and restricted artifact references.

## Open Decisions

### Decision 1 - Primary Storage Split

Decide which records live in relational storage, graph storage, object storage, and broker persistence.

### Decision 2 - Model Routing Defaults

**Closed (2026-07-23):** LiteLLM gateway + published local/cloud profiles under
`backend/configs/model-routing/` (see `10-model-routing-profiles-with-litellm.md`). Closes GAP-003 / DEC-001.

### Decision 3 - WeightProfile Governance

Define who can create, approve, and change memory and graph retrieval weighting profiles.

### Decision 4 - Schema Registry Implementation

**Closed (2026-07-23):** Repository-directory catalog
(`12-schema-registry-architecture.md` + `backend/tools/schema-registry/catalog.json`).
Closes GAP-008.

### Decision 5 - SDK Scope And First Integration Targets

Define the first supported SDK languages, package registries, IDE integrations, CI integrations, ticketing integrations, external agent integrations, and adapter harness scope.

### Decision 6 - Development Port Base Policy

Choose the default AgentCore development port base and override behavior for local machines.

## Tracking Rule

Every open decision should become a Decision record before implementation starts. Every risk should have an owner, mitigation, severity, and review date.

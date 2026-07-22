---
doc_id: ac.doc.ops.data-retention-backup-and-disaster-recovery
title: Data Retention, Backup, and Disaster Recovery
doc_type: standard
status: active
schema_version: '1.0'
owner: platform-docs
summary: AgentCore stores operational evidence, code graph data, memory, documentation links,
  rules, approvals, and broker events. The platform must define how long data is retained,
  how it is backed up, and how it is restored after failure.
tags:
- standard
- ops
phase: 09-platform-governance-operations
canonical_path: docs/09-platform-governance-operations/04-data-retention-backup-and-disaster-recovery.md
lifecycle_lane: current
concern_lane: standard
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols: []
---

# Data Retention, Backup, and Disaster Recovery

## Purpose

AgentCore stores operational evidence, code graph data, memory, documentation links, rules, approvals, and broker events. The platform must define how long data is retained, how it is backed up, and how it is restored after failure.

## Data Classes

- Structured work records: Activity, WorkLog, Decision, Issue, Task.
- Memory records: MemoryItem, SemanticFact, ContextBundle, WeightProfile.
- Code graph records: File, Class, Function, Method, relationships, embeddings.
- Documentation records: Doc, DocAnchor, DriftFinding.
- Governance records: Policy, RuleEvaluation, EscalationTicket, approval records.
- Broker records: Channel, Subscription, DeliveryAttempt, DeadLetter.
- Evidence artifacts: logs, diffs, test outputs, generated artifacts.

## Retention Rules

Retention should vary by data class and sensitivity.

General principles:

- Decisions and approvals should be retained longer than routine Activities.
- Security and compliance evidence may require extended retention.
- Prompt-visible summaries can expire earlier than audit evidence.
- Deprecated memory can be excluded from prompts while retained for audit.
- Customer data should follow privacy and deletion rules.

## Backup Requirements

Backups should include:

- primary structured database,
- Neo4j graph database,
- broker state when persistent,
- object/artifact storage,
- configuration profiles,
- schema versions,
- encryption metadata.

## Restore Requirements

A restore is incomplete unless indexes, graph relationships, memory state, and broker replay state remain consistent.

Restore validation should check:

- entity count consistency,
- graph relationship consistency,
- latest migration version,
- ability to reconstruct audit timeline,
- ability to build a ContextBundle,
- ability to run drift detection,
- ability to publish and consume broker events.

## Disaster Recovery Strategy

The platform should define RPO and RTO per environment. Production needs stricter recovery targets than development.

Recovery procedure:

1. Stop writes if corruption is suspected.
2. Snapshot current failed state for forensics.
3. Restore latest valid backup.
4. Replay safe event logs if available.
5. Verify schema and graph consistency.
6. Resume services gradually.
7. Create incident report and follow-up Tasks.

## Acceptance Criteria

- Backups are scheduled and monitored.
- Restore is tested regularly.
- Audit evidence can be restored with source references.
- Deprecated memory remains auditable within retention period.
- Customer data deletion requirements are enforceable.

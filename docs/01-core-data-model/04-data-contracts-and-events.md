---
doc_id: ac.doc.core.data-contracts-and-events
title: Core Data Model - Data Contracts and Events
doc_type: contract
status: active
schema_version: '1.0'
owner: platform-docs
summary: '- `Agent(id, vendor, model, capabilities, trust_level, owner)` - `Activity(id, agent_id,
  task_id, timestamp, action_summary, files_changed, command_refs, test_refs, artifact_refs)`
  - `WorkLog(id, session_id, agent_id, summary, blockers, followups, confidence)` - `Decision(id,
  tit.'
tags:
- contract
- core
phase: 01-core-data-model
canonical_path: docs/01-core-data-model/04-data-contracts-and-events.md
lifecycle_lane: current
concern_lane: contract
audience_lane:
- platform-engineering
- agents
authority: normative
visibility: internal
linked_symbols: []
doc_version: 1.0.0
updated_at: '2026-07-24'
---

# Core Data Model - Data Contracts and Events


## Purpose

- `Agent(id, vendor, model, capabilities, trust_level, owner)` - `Activity(id, agent_id, task_id, timestamp, action_summary, files_changed, command_refs, test_refs, artifact_refs)` - `WorkLog(id, session_id, agent_id, summary, blockers, followups, confidence)` - `Decision(id, tit.

## Core Entities

- `Agent(id, vendor, model, capabilities, trust_level, owner)`
- `Activity(id, agent_id, task_id, timestamp, action_summary, files_changed, command_refs, test_refs, artifact_refs)`
- `WorkLog(id, session_id, agent_id, summary, blockers, followups, confidence)`
- `Decision(id, title, context, options_considered, chosen_option, consequences, generated_rules, linked_entities, supersedes)`
- `Issue(id, title, description, severity, discovered_by, evidence_refs, status, owner)`
- `Task(id, issue_id, title, assignee_type, instructions, dependencies, status, acceptance_criteria)`

Collaboration-surface extensions (ChangeSet, ReviewThread, ReviewComment, DiscussionComment, WorkLabel, WorkMilestone) are specified in `08-changeset-review-and-discussion-contracts.md` and must be merged into this catalog when implementation starts.

## Events

- `activity.recorded`
- `worklog.created`
- `decision.created`
- `decision.superseded`
- `issue.discovered`
- `issue.triaged`
- `task.created`
- `task.completed`
- `audit.timeline_requested`

## Contract Rules

- Every event includes `event_id`, `event_type`, `occurred_at`, `source`, `correlation_id`, and `tenant_id`.
- Every entity includes `id`, `created_at`, `updated_at`, `status`, and `source_refs` where applicable.
- Large logs, diffs, and generated artifacts are stored as artifact references rather than inline payloads.
- Security-sensitive fields must be redacted before records are used in prompts, dashboards, or events.
- Decisions are immutable except for lifecycle fields such as status, superseded_by, and review metadata.

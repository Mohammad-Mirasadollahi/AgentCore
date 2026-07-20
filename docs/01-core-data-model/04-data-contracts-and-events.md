# Core Data Model - Data Contracts and Events

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

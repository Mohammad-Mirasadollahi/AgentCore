# 01 - Core Data Model Index

## Mission

Turn every agent action, architectural reason, discovered problem, and executable assignment into durable structured knowledge.

## Files

- `01-feature-specification.md` defines the feature scope and functional requirements.
- `02-high-level-design.md` defines actors, components, boundaries, integrations, and system-level flow.
- `03-low-level-design.md` defines modules, state machines, validation rules, idempotency, and failure handling.
- `04-data-contracts-and-events.md` defines entities, contracts, and events.
- `05-risks-challenges-and-acceptance.md` defines challenges, mitigations, and acceptance criteria.
- `06-detailed-section-design.md` provides deep rationale, lifecycle details, examples, edge cases, and phase output.
- `07-agent-collaboration-work-surface.md` defines the AgentCore-native Issue/Task/AgentTicket/ChangeSet/Review/Comment/Label surface for agents (GitHub-like in role, not GitHub as SoR).
- `08-changeset-review-and-discussion-contracts.md` defines contracts, state machines, commands, queries, and events for ChangeSet, reviews, discussion, and labels.

## Features Covered

- Activity and Work Log
- Decision Tracking
- Issue and Task Separation
- Agent collaboration work surface (ChangeSet, ReviewThread, DiscussionComment, WorkLabel)

## Related Technical Logic

- `../06-technical-logic/01-core-data-model-technical-logic.md` explains entity invariants, write paths, state transitions, idempotency, audit reconstruction, and task decomposition logic.
- External tracker/VCS projection rules: `../05-interoperability-ecosystem/10-external-vcs-and-tracker-mapping.md`.

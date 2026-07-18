# Core Data Model - Risks, Challenges, and Acceptance

## Challenges

- Avoid logging secrets or sensitive terminal output while preserving enough evidence for audits.
- Prevent Activity records from becoming noisy chat transcripts.
- Keep Issue and Task semantics strict so orchestration does not confuse risk discovery with execution.
- Preserve Decision rationale without freezing the architecture when a newer Decision supersedes an older one.

## Mitigation Strategy

- Redact at ingestion boundaries.
- Store raw evidence as controlled artifact references.
- Enforce schemas for Issue and Task creation.
- Require Decisions to include context, alternatives, consequences, and supersession rules.
- Provide audit queries that join Activities, Decisions, Issues, and Tasks by correlation ID.

## Acceptance Criteria

- Every agent session produces at least one WorkLog and zero or more linked Activity records.
- A production incident can be reconstructed from Activity, Decision, Issue, and Task records without reading raw chat history.
- Every critical Issue has one or more Tasks or a documented reason for human escalation.
- Decisions can generate prompt rules and can be superseded without being physically deleted.

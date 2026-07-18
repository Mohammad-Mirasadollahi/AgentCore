# 04 - Common Context Data Contracts And Events

## Contract Families

Contracts should be published through `backend/packages/common-context/contracts` and versioned through the schema registry.

Required families:

- CommonItemRequest and CommonItemResponse
- CommonItemVersion
- CommonContextScope
- ApplicabilityRule
- ReuseScoreBreakdown
- ContextBundleRequest
- ContextBundleResponse
- CommonContextConflict
- CommonContextAuditRecord
- CommonContextUsageMetric

## Event Names

- `CommonItemCreated`
- `CommonItemUpdated`
- `CommonItemApproved`
- `CommonItemRejected`
- `CommonItemPromotedFromRepeatedInstruction`
- `CommonItemDeprecated`
- `CommonItemSuppressedForScope`
- `CommonContextBundleResolved`
- `CommonContextConflictDetected`
- `CommonContextEffectivenessRecorded`

## Event Metadata

Every event must include event_id, event_type, event_version, occurred_at, actor_id, project_id, scope_type, scope_id, correlation_id, causation_id, source_service, and audit_record_id.

## Compatibility Rules

Contracts must be additive by default. Breaking changes require a new event version, migration notes, SDK generation updates, contract tests, and release notes.

# 05 - Common Context Governance And Operational Rules

## Governance Principles

Common Context changes how agents behave, so it must be governed like product and architecture policy. The system must never silently turn every repeated phrase into an enforced rule.

## Approval Rules

- Project-scoped low-risk items may be auto-proposed but should still be visible for review.
- Cross-project or project-group items require explicit approval.
- Security, privacy, deployment, and access-control items require owner approval.
- Mandatory governance items require change records and audit evidence.

## Isolation Rules

Common items are private to their project unless explicitly bound to a project group. Shared project groups must define member projects, allowed item types, owners, and revocation rules.

## Override Rules

A task-specific instruction can override common context when it is explicit and authorized. The override must be recorded with the reason. Mandatory safety or isolation policies cannot be overridden by ordinary task text.

## Retention Rules

Common items should have lifecycle status: proposed, approved, active, suppressed, deprecated, archived. Items with low usage, low confidence, or repeated conflicts should be reviewed automatically.

## Reporting Rules

Common Context must report number of repeated instructions converted to common items, avoided repetitions, estimated token savings, conflicts resolved, agent failures prevented, and stale or low-confidence items.

## Operational Risk

The main risk is over-injection. The resolver must prefer small, relevant, high-confidence items and expose suppression controls in the admin interface.

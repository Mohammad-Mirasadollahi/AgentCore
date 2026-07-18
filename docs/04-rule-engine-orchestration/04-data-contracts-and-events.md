# Rule Engine and Orchestration - Data Contracts and Events

## Core Entities

- `Policy(id, title, natural_language_rule, scope, severity, owner, examples, evaluation_mode)`
- `RuleEvaluation(id, policy_id, subject_ref, verdict, confidence, rationale, evidence_refs)`
- `EscalationTicket(id, evaluation_id, approver, status, options, deadline, decision_reason)`
- `ImpactMap(id, change_ref, affected_entities, risk_level, generated_task_refs)`
- `Runbook(id, trigger, steps, compensation_steps, required_approvals)`

## Events

- `policy.created`
- `policy.updated`
- `rule.evaluated`
- `risk.flagged`
- `escalation.created`
- `approval.resolved`
- `impact.map_created`
- `task.routed`
- `runbook.started`
- `runbook.completed`

## Contract Rules

- Every Policy must have an owner, severity, scope, and examples.
- Every LLM-based RuleEvaluation must store rationale and evidence references.
- Escalation tickets must present clear approve/reject options and a deadline.
- Impact maps must include confidence and avoid generating low-confidence tasks by default.
- Runbooks must define compensation steps for partially completed workflows.

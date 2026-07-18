# 24 - Admin Web Interface And Agent Control Surface

## Purpose

AgentCore must provide a professional web interface that acts as the operational control surface for humans supervising agents, memory, tasks, rules, tickets, automation, reports, and audit evidence. The interface must show exactly what agents and system components did, why they did it, which evidence was used, what changed, which tasks remain open, and how user corrections should affect future behavior.

This is not a marketing dashboard. It is a product and engineering control plane for traceability, governance, correction, and agent supervision.

## Corrected Requirement

The raw user requirement can be formalized as follows:

AgentCore must include a web interface where authorized users can track every meaningful action performed by agents or the platform, manage memory and tickets for agents, create and assign tasks, define rules, inspect decisions, correct wrong behavior, provide feedback, and teach the system that a specific answer, assumption, rule, memory item, scope, or task decomposition was wrong. Corrections must become structured feedback that can update memory confidence, retrieval ranking, rule behavior, task state, documentation drafts, or future agent behavior. The UI must expose audit evidence and project scope for every action.

## Professional Audience

This document is written for:

- product designers defining information architecture, workflows, state models, and operator experience.
- frontend engineers implementing admin-console views, state handling, filters, permissions, and interaction models.
- backend engineers implementing APIs, event feeds, query models, feedback contracts, and audit access.
- platform operators using the control surface to supervise automation.
- engineering leaders and reviewers tracking agent work and quality.
- security reviewers validating permission boundaries and high-risk actions.

## Product Goals

The web interface should let authorized users:

- track every meaningful agent and system action.
- inspect Activity, WorkLog, Decision, Issue, Task, MemoryItem, QuestionMemory, Rule, WorkBatch, AutomationJob, Connector, Report, and AuditRecord objects.
- manage memory items, repeated questions, FAQ candidates, and generated answers.
- manage tickets and tasks for agents and humans.
- create new tasks for agents with structured context and acceptance criteria.
- correct wrong answers, wrong memory retrieval, wrong documentation drafts, wrong task decomposition, wrong rules, and wrong project scope.
- define and test rules.
- inspect batches and deferred reviews.
- inspect connector health and agent registrations.
- manage project scope and ProjectGroups.
- view reports comparing outcomes with and without AgentCore.
- audit why the system made a decision or selected a memory item.

## Non-Goals

- The web interface should not bypass service APIs or read databases directly.
- The web interface should not expose raw secrets or sensitive prompts.
- The web interface should not allow high-risk rule, memory, or connector changes without permission and audit.
- The web interface should not hide active project or ProjectGroup scope.
- The web interface should not make unstructured free-text corrections that cannot affect system behavior.

## Primary Roles And Permissions

| Role | Primary Capabilities |
| --- | --- |
| workspace_admin | manage projects, ProjectGroups, users, connectors, policies, reports |
| project_owner | manage project memory, tasks, rules, agents, reports, and settings |
| developer | inspect actions, tasks, docs, memory, batches, and provide corrections |
| reviewer | review code, docs, tasks, decisions, and agent outputs |
| security_reviewer | review high-risk rules, approvals, auth changes, and sensitive evidence |
| platform_operator | manage automation jobs, deployment status, connectors, diagnostics |
| product_manager | inspect reports, tasks, outcomes, bottlenecks, and decisions |
| integration_owner | manage external connectors and capability mappings |
| agent_supervisor | assign work to agents, inspect agent performance, correct behavior |

Every view and action must declare required permission.

## Information Architecture

Recommended navigation:

- Overview.
- Projects.
- Activity Timeline.
- Work Logs.
- Decisions.
- Issues.
- Tasks And Tickets.
- Memory.
- Repeated Questions.
- Documentation Drafts.
- Code Graph.
- Rules.
- Agents.
- Connectors.
- Work Batches.
- Automation Jobs.
- Reports.
- Audit.
- Settings.

Global UI requirements:

- active tenant indicator.
- active workspace indicator.
- active project or ProjectGroup indicator.
- search scoped by default.
- cross-project warning when ProjectGroup scope is active.
- permission-aware navigation.
- evidence drilldown available where permitted.

## Object Detail Pages

Each major object should have a detail page.

### Activity Detail

Should show:

- actor.
- action type.
- timestamp.
- project scope.
- source surface.
- changed files or symbols.
- command or event source.
- result.
- related WorkBatch.
- related Task.
- evidence.
- correlation ID.

### Memory Detail

Should show:

- memory type.
- scope.
- content summary.
- evidence references.
- confidence.
- freshness.
- score factors.
- retrieval history.
- correction history.
- related questions.
- status.

Allowed actions:

- pin.
- archive.
- mark stale.
- correct.
- split.
- merge.
- request review.
- create Task.

### Task Detail

Should show:

- title.
- owner.
- assigned agent or human.
- status.
- priority.
- acceptance criteria.
- dependencies.
- related memory.
- related decisions.
- related code symbols.
- related docs.
- evidence.
- activity timeline.
- external ticket link.

Allowed actions:

- assign to agent.
- assign to human.
- change priority.
- add dependency.
- add acceptance criteria.
- approve completion.
- reopen.
- create child task.
- link evidence.

### Rule Detail

Should show:

- rule name.
- owner.
- version.
- scope.
- status.
- condition.
- severity.
- escalation path.
- examples.
- evaluations.
- false positives.
- false negatives.
- change history.

Allowed actions:

- create version.
- test rule.
- run in shadow mode.
- enable.
- disable with approval when high risk.
- create correction.
- link to Task or Gap.

### Agent Detail

Should show:

- agent identity.
- allowed project scopes.
- capabilities.
- assigned tasks.
- recent actions.
- success rate.
- correction rate.
- token usage.
- memory usage.
- connector dependencies.
- current status.

Allowed actions:

- assign task.
- pause agent.
- revoke scope.
- update capabilities.
- inspect recent work.
- create correction.

## Activity Timeline

The Activity Timeline is the primary tracking view.

It should support:

- chronological event stream.
- filters by project, actor, agent, action type, task, file, symbol, rule, connector, batch, and time range.
- grouping by WorkBatch.
- diff and evidence links.
- correlation ID search.
- audit-sensitive markers.
- failed action highlighting.
- cross-project access markers.

The timeline should answer:

- what happened.
- who or what did it.
- when it happened.
- why it happened.
- which evidence supports it.
- what changed afterward.

## Memory Management Workflow

Users should be able to manage agent memory deliberately.

Memory actions:

- approve memory.
- reject memory.
- correct memory.
- mark stale.
- archive.
- pin.
- split.
- merge.
- change owner.
- create Task from memory issue.
- create Gap from missing evidence.

Correction workflow:

1. user selects memory item.
2. user chooses correction type.
3. user provides corrected statement or reason.
4. system shows affected retrieval, FAQ, and dependent answers.
5. user confirms impact.
6. system creates FeedbackRecord.
7. memory confidence or status changes.
8. related QuestionMemory or answers are updated.
9. audit event is recorded.

## Repeated Questions And FAQ Workflow

The Repeated Questions view should support:

- normalized question list.
- observation count.
- distinct actor count.
- curiosity score.
- FAQ score.
- answer status.
- missing documentation status.
- evidence status.
- owner.
- next action.

Allowed actions:

- approve FAQ.
- reject FAQ.
- edit answer.
- split question group.
- merge duplicate question.
- create documentation task.
- create KnowledgeGap.
- mark low value.
- request investigation.

## Task And Ticket Management Workflow

The Tasks And Tickets view should support agent-directed work.

Capabilities:

- create task for agent.
- create task for human.
- set acceptance criteria.
- attach context bundle.
- attach memory items.
- attach code symbols.
- attach docs.
- attach decision references.
- link external ticket.
- track status.
- approve or reject completion.
- reopen with correction.

Agent task creation should require:

- project scope.
- objective.
- constraints.
- acceptance criteria.
- required evidence.
- allowed tools or connectors.
- risk level.

## Feedback And Learning Control

Users must be able to tell the system what was wrong and how it should behave next time.

Correction types:

- wrong_answer.
- wrong_memory.
- stale_memory.
- wrong_scope.
- wrong_task_decomposition.
- wrong_rule_interpretation.
- wrong_documentation_draft.
- wrong_code_impact_analysis.
- wrong_connector_mapping.
- missing_context.
- unsafe_action.

FeedbackRecord should include:

- feedback_id.
- target_type.
- target_ref.
- correction_type.
- corrected_value.
- reason.
- project_scope.
- created_by.
- created_at.
- affected_memory_refs.
- affected_rule_refs.
- affected_task_refs.
- status.

Feedback effects may include:

- lower answer confidence.
- supersede MemoryItem.
- update QuestionAnswer.
- create Gap.
- create Task.
- adjust retrieval feedback signals.
- create rule improvement suggestion.
- require human review.

The system should learn through explicit structured feedback, not hidden mutation.

## Rule Management Workflow

Users should be able to define rules for agents and workflows.

Rule creation should include:

- name.
- scope.
- owner.
- description.
- condition.
- severity.
- examples.
- allowed actions.
- blocked actions.
- escalation target.
- test cases.
- rollout mode.

Rollout modes:

- draft.
- shadow.
- active.
- disabled.
- deprecated.

High-risk rule changes require approval and audit.

## Work Batch Management

The Work Batches view should show:

- active batches.
- batch type.
- objective.
- readiness score.
- boundary signals.
- changed files.
- changed symbols.
- deferred memory consolidation.
- deferred documentation generation.
- deferred code review.
- immediate guardrails.
- failed deferred actions.

Allowed actions:

- force consolidation.
- mark ready for review.
- request code review.
- request documentation generation.
- split batch.
- merge batches.
- cancel batch.
- retry failed deferred action.

## Automation Jobs

The Automation Jobs view should show:

- job type.
- status.
- current step.
- risk level.
- approval requirement.
- logs.
- evidence report.
- retryability.
- failure reason.
- repair hint.

Job types:

- installation.
- connector registration.
- migration.
- upgrade.
- drift detection.
- repair.
- diagnostics.

## Reports

Reports should be accessible from the web interface.

Report categories:

- initial code generation speed.
- bug reduction.
- architecture quality.
- rework reduction.
- token consumption.
- documentation drift.
- connector health.
- memory quality.
- agent productivity.
- approval bottlenecks.

Reports must show scope, baseline, time range, sample size, caveats, and evidence drilldown.

## API And Query Model

The admin-console should use public APIs and query models.

Forbidden:

- direct database reads.
- direct service-internal imports.
- bypassing authorization in frontend filters.
- unscoped queries.

Required query capabilities:

- activity timeline query.
- object detail query.
- memory management query.
- task board query.
- rule management query.
- feedback mutation.
- audit search query.
- report query.
- project scope query.

## Product State Requirements

Every major view should support:

- loading.
- empty.
- permission_denied.
- degraded.
- error.
- partial_data.
- stale_data.
- audit_sensitive.
- project_scope_warning.
- project_group_scope_warning.
- action_requires_approval.
- action_completed.
- action_failed.

## Security And Audit Requirements

Security requirements:

- every view enforces permission at API level.
- project scope is mandatory for scoped objects.
- cross-project access shows warning and audit marker.
- sensitive evidence is redacted unless user has permission.
- high-risk changes require approval.
- all corrections create audit events.
- rule changes are versioned.
- memory changes preserve previous value for audit.

## Acceptance Criteria

The web interface is acceptable when:

- users can track every meaningful agent and platform action from the Activity Timeline.
- users can inspect object detail pages for Activity, WorkLog, Decision, Issue, Task, MemoryItem, QuestionMemory, Rule, WorkBatch, AutomationJob, Connector, Report, and AuditRecord.
- users can manage memory, repeated questions, FAQ candidates, tasks, tickets, rules, agents, connectors, batches, automation jobs, reports, and audit records.
- users can create tasks for agents with scope, objective, constraints, acceptance criteria, evidence, tools, and risk level.
- users can correct wrong behavior through structured FeedbackRecord objects.
- corrections affect future behavior through memory confidence, retrieval feedback, rule suggestions, task state, gaps, or review workflows.
- users can define and test rules, including shadow mode and approval-controlled activation.
- project or ProjectGroup scope is always visible and enforced.
- high-risk operations are permission-controlled, approval-gated, and auditable.
- admin-console uses public APIs and never reads service databases directly.

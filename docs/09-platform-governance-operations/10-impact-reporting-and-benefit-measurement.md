# 10 - Impact Reporting And Benefit Measurement

## Purpose

AgentCore must prove its value with measurable, auditable, scope-aware reporting. The platform should help teams compare engineering outcomes with AgentCore enabled versus disabled, or with specific AgentCore capabilities enabled versus disabled. Reports must show whether the platform improves initial code generation speed, bug reduction, architecture quality, rework reduction, and token consumption.

This document defines the measurement framework, KPI definitions, event instrumentation, baseline strategy, comparison methodology, dashboard requirements, evidence model, interpretation rules, and acceptance criteria.

## Corrected Requirement

The raw user requirement can be formalized as follows:

AgentCore must include an impact reporting system that measures the practical difference between using and not using the platform. The system should not only show activity counts. It should measure outcome quality and engineering efficiency across defined scopes. The required metrics are initial code generation speed, bug reduction, architecture quality, rework reduction, and token consumption. Each metric must have a clear definition, data source, baseline, time range, project scope, confidence caveat, and evidence drilldown.

The reporting system should be useful for engineering leaders, product owners, platform operators, and architects who need to decide whether AgentCore is improving real delivery outcomes or only adding process overhead.

## Professional Audience

This document is written for:

- engineering leaders measuring productivity and quality.
- software architects measuring architecture health and boundary integrity.
- platform operators measuring adoption, reliability, and token efficiency.
- product managers measuring workflow improvements and bottlenecks.
- data analysts building dashboards and metric pipelines.
- finance or operations stakeholders evaluating AI tool cost and benefit.
- security and governance reviewers validating evidence and auditability.

## Measurement Principles

Reporting must follow these principles:

- Measure outcomes, not only activity.
- Always show scope, baseline, and time range.
- Never mix unrelated projects without explicit ProjectGroup scope.
- Segment results by task complexity where possible.
- Pair speed metrics with quality metrics.
- Pair token savings with success and correction metrics.
- Link aggregate numbers to evidence.
- Separate early detection from defect creation.
- Make caveats visible instead of hiding uncertainty.
- Avoid claiming causality when only correlation is available.

## Required Business Questions

The reporting system should answer:

- Did initial code generation become faster.
- Did bugs decrease or shift earlier in the lifecycle.
- Did architecture quality improve.
- Did rework decrease.
- Did token consumption decrease.
- Did documentation drift decrease.
- Did repeated questions decrease after FAQ memory and documentation generation.
- Did agent work become easier to audit.
- Did project context retrieval become more accurate.
- Did automation overhead exceed measured benefit.

## Metric Families

| Metric Family | Primary Question | Required Output |
| --- | --- | --- |
| Initial Code Generation Speed | How fast does a task reach first useful implementation | duration, percentile, baseline delta, evidence |
| Bug Reduction | Are fewer defects introduced or escaping | defect counts, severity, phase found, baseline delta |
| Architecture Quality | Is the system becoming structurally healthier | boundary violations, coupling, contract drift, decisions |
| Rework Reduction | Is repeated work decreasing | reopen rate, duplicate work, repeated fixes, repeated questions |
| Token Consumption | Is context and model usage more efficient | tokens, cost, cache hit, useful context ratio, quality guardrail |

## Scope Model

Every report must declare scope.

Required scope fields:

- tenant_id.
- workspace_id.
- project_id or project_group_id.
- included repositories.
- included agents.
- included human roles.
- included task types.
- included feature flags.
- excluded data.
- time range.
- baseline window.
- comparison method.

A report that aggregates across projects without explicit ProjectGroup policy is invalid.

## Baseline And Comparison Methods

AgentCore should support multiple comparison methods.

| Method | Description | Best Use |
| --- | --- | --- |
| before_after_project | compare project before and after AgentCore adoption | early rollout |
| control_project | compare similar project with no AgentCore | stronger organizational comparison |
| feature_flag_split | compare same project with a feature enabled or disabled | feature impact measurement |
| agent_workflow_comparison | compare agent workflow with and without memory, docs, or rules | subsystem evaluation |
| manual_vs_agent_assisted | compare human-only or manual workflow to AgentCore-assisted workflow | productivity analysis |
| cohort_by_task_type | compare similar task classes | reducing complexity bias |

Every comparison must state limitations.

Common limitations:

- task complexity differs.
- team maturity differs.
- repository maturity differs.
- release phase differs.
- measurement instrumentation changed.
- small sample size.
- quality moved from late detection to early detection.

## KPI 1: Initial Code Generation Speed

### Definition

Initial code generation speed measures how quickly a task reaches first useful implementation. It should not only measure first output. It should measure output that reaches a meaningful engineering state.

Recommended KPIs:

- time_to_first_code_draft.
- time_to_first_compilable_state.
- time_to_first_test_run.
- time_to_first_passing_test.
- time_to_review_ready_state.
- time_to_first_accepted_patch.
- clarification_cycles_before_first_draft.

### Required Segmentation

Segment by:

- project.
- repository.
- agent type.
- task type.
- complexity band.
- risk level.
- new feature vs bug fix vs refactor.
- language or framework.

### Data Sources

- TaskCreated event.
- WorkBatch opened and completed events.
- Activity records.
- code graph change events.
- test run events.
- review-ready events.
- PR or patch events.
- WorkLog summaries.

### Interpretation Rules

- Faster first draft is positive only if bug, rework, and review rejection metrics do not worsen.
- First text output should not count as implementation speed unless it produces code evidence.
- Exploratory tasks should be reported separately from well-scoped implementation tasks.

## KPI 2: Bug Reduction

### Definition

Bug reduction measures whether AgentCore reduces defects or moves detection earlier in the lifecycle.

Recommended KPIs:

- defects_found_in_review.
- defects_found_by_tests.
- escaped_defects_after_release.
- regression_count.
- severity_weighted_defect_score.
- bug_reopen_rate.
- policy_prevented_bug_count.
- security_issue_prevented_count.

### Defect Phase Classification

Each bug should include phase found:

- during_generation.
- during_agent_self_review.
- during_automated_tests.
- during_human_review.
- during_staging.
- after_release.
- during_incident.

Early detection may increase reported defects while reducing escaped defects. Reports must explain this.

### Data Sources

- Issue records.
- test reports.
- CI failures.
- review comments.
- rule evaluations.
- incident records.
- audit evidence.
- rollback events.

### Interpretation Rules

- An increase in review-time defects can be good if release-time defects decrease.
- Defect counts should be severity-weighted.
- Bug reduction should be measured per task complexity band.

## KPI 3: Architecture Quality

### Definition

Architecture quality measures whether AgentCore helps preserve modularity, contract integrity, documentation alignment, and system design coherence.

Recommended KPIs:

- dependency_boundary_violation_count.
- forbidden_import_count.
- circular_dependency_count.
- contract_drift_count.
- undocumented_public_api_count.
- stale_architecture_decision_count.
- unresolved_architecture_gap_count.
- code_graph_modularity_score.
- service_ownership_coverage.
- docs_to_symbol_coverage.
- migration_risk_score.

### Architecture Health Dimensions

Dimensions:

- modularity.
- coupling.
- contract stability.
- documentation coverage.
- decision traceability.
- ownership clarity.
- migration safety.
- project isolation compliance.

### Data Sources

- code graph snapshots.
- dependency boundary checks.
- docs graph.
- contract registry.
- decision records.
- gap analysis.
- CI architecture checks.
- review outcomes.

### Interpretation Rules

- Architecture quality is not a single subjective score.
- Composite scores must show component metrics.
- Boundary violations should be normalized by repository size and change volume.
- A temporary increase in gaps can be positive if it means hidden risks became visible.

## KPI 4: Rework Reduction

### Definition

Rework reduction measures whether AgentCore reduces repeated effort, duplicate fixes, repeated questions, reopened tasks, and avoidable rediscovery.

Recommended KPIs:

- reopened_task_rate.
- duplicate_task_count.
- repeated_fix_count.
- revert_count.
- repeated_question_count.
- repeated_documentation_drift_count.
- repeated_rule_false_positive_count.
- repeated_connector_failure_count.
- correction_rate_for_agent_outputs.
- time_spent_on_clarification.

### Data Sources

- Task history.
- WorkBatch history.
- WorkLog records.
- QuestionMemory records.
- documentation drift records.
- git activity summaries.
- rule feedback.
- connector validation history.
- human correction records.

### Interpretation Rules

- Rework should decrease after memory consolidation, QuestionMemory, FAQ memory, docs sync, and stronger contracts become active.
- Reopened tasks should be separated into legitimate scope changes versus quality failures.
- Repeated questions should be segmented by unanswered, answered, stale, and FAQ-promoted status.

## KPI 5: Token Consumption

### Definition

Token consumption measures how efficiently AgentCore uses model context and model calls while preserving or improving output quality.

Recommended KPIs:

- total_tokens_per_task.
- input_tokens_per_task.
- output_tokens_per_task.
- tokens_per_successful_patch.
- tokens_per_accepted_review.
- tokens_per_documentation_update.
- prompt_cache_hit_rate.
- context_bundle_size.
- useful_context_ratio.
- discarded_context_ratio.
- repeated_question_token_cost.
- model_tier_mix.
- estimated_model_cost.

### Quality Guardrails

Token savings are valid only when quality does not degrade.

Pair token metrics with:

- task success rate.
- human correction rate.
- bug rate.
- rework rate.
- answer confidence.
- review rejection rate.

### Data Sources

- model provider usage records.
- prompt assembly logs.
- ContextBundle records.
- prompt cache events.
- Memory retrieval logs.
- QuestionMemory records.
- WorkBatch records.
- task outcome records.

### Interpretation Rules

- Lower tokens are not automatically better.
- Token savings should be compared against task success and defect outcomes.
- Reports should separate deterministic context reduction from model quality degradation.

## Reporting Data Model

### MetricDefinition

Recommended contract:

    MetricDefinition:
        metric_id
        name
        family
        description
        numerator_definition
        denominator_definition
        unit
        aggregation_method
        required_scope_fields
        required_evidence_types
        owner
        version
        status

### MeasurementRun

Recommended contract:

    MeasurementRun:
        run_id
        metric_ids
        tenant_id
        workspace_id
        project_id
        project_group_id
        time_range
        baseline_range
        comparison_method
        feature_flags
        sample_size
        exclusions
        generated_at
        generated_by
        confidence_notes

### MetricResult

Recommended contract:

    MetricResult:
        result_id
        run_id
        metric_id
        scope
        value
        baseline_value
        delta_absolute
        delta_percent
        direction
        confidence_level
        caveats
        evidence_refs

### ReportEvidenceRef

Recommended contract:

    ReportEvidenceRef:
        evidence_id
        evidence_type
        source_ref
        metric_id
        contribution_type
        timestamp
        scope

## Reporting Events

Recommended events:

- reporting.measurement_requested
- reporting.measurement_completed
- reporting.metric_definition_changed
- reporting.baseline_created
- reporting.dashboard_viewed
- reporting.report_exported
- reporting.evidence_drilldown_opened
- reporting.caveat_acknowledged

Event rules:

- Events must include project or project group scope.
- Exported reports must include metric definitions and caveats.
- Evidence drilldown should be auditable for sensitive projects.

## Instrumentation Requirements

The system must instrument these lifecycle events:

- task created.
- task started.
- first code draft created.
- first test run started.
- first passing test recorded.
- review-ready state reached.
- review defect recorded.
- test defect recorded.
- release defect recorded.
- task reopened.
- task completed.
- WorkBatch opened.
- WorkBatch completed.
- ContextBundle built.
- prompt cache hit or miss.
- memory item retrieved.
- question observed.
- FAQ answer reused.
- documentation drift detected.
- architecture boundary violation detected.

Without instrumentation, the report should mark the metric as incomplete rather than silently estimating.

## Dashboard Requirements

Dashboards should include:

- executive summary.
- project-level comparison.
- project group comparison.
- before and after view.
- feature flag comparison.
- metric family tabs.
- time range selector.
- baseline selector.
- evidence drilldown.
- caveat panel.
- export action.
- metric definition view.

Dashboard states:

- loading.
- no_data.
- partial_data.
- insufficient_baseline.
- permission_denied.
- scoped_project_view.
- scoped_project_group_view.
- stale_instrumentation.
- ready.

## Product Experience

The reporting UI should make metrics trustworthy.

Each chart should show:

- metric definition.
- current value.
- baseline value.
- delta.
- trend.
- sample size.
- scope.
- time range.
- caveats.
- evidence link.

Users should be able to:

- select scope.
- select baseline.
- compare with and without AgentCore.
- compare feature flags.
- drill into evidence.
- export report.
- mark caveat acknowledged.
- create a follow-up Task from a bad metric.
- create a Gap when measurement is incomplete.

## Example: With And Without AgentCore Report

Scenario:

- Project A used AgentCore for four weeks.
- The previous four weeks are used as baseline.
- Task complexity is segmented into small, medium, and large.

Report output:

- initial code generation speed improved 22 percent for medium tasks.
- escaped defects decreased 18 percent.
- review-time defects increased 9 percent, explained as earlier detection.
- dependency boundary violations decreased 35 percent.
- reopened tasks decreased 14 percent.
- total tokens per accepted patch decreased 28 percent.
- caveat: sample size for large tasks is low.

The report must link every number to MeasurementRun, MetricResult, and evidence references.

## Anti-Metrics And Misuse Risks

Avoid these mistakes:

- counting generated lines of code as productivity without quality checks.
- claiming bug reduction when only detection moved earlier.
- treating lower token usage as success when corrections increased.
- comparing unrelated projects without normalization.
- hiding incomplete instrumentation.
- aggregating tenant or project data without authorization.
- using reports to punish teams instead of improving workflows.

## Acceptance Criteria

Impact reporting is acceptable when:

- reports cover initial code generation speed, bug reduction, architecture quality, rework reduction, and token consumption.
- each metric has a formal definition, owner, unit, evidence type, and aggregation method.
- every report declares scope, baseline, comparison method, time range, sample size, and caveats.
- reports can compare with and without AgentCore or with and without specific AgentCore capabilities.
- metrics are segmented by project, project group, agent, repository, task type, complexity, and time range where data allows.
- dashboards allow drilldown from summary metric to source evidence.
- incomplete instrumentation is shown explicitly.
- token savings are evaluated together with success rate, correction rate, bug rate, and rework rate.
- project isolation rules are enforced for all reports.

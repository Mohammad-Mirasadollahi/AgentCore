# Memory and Context - Data Contracts and Events

## Core Entities

- `MemoryItem(id, type, scope, content, confidence, source_refs, status, expires_at)`
- `SemanticFact(id, subject, predicate, object, evidence_refs, supersedes, status)`
- `ContextBundle(id, task_id, static_section_version, dynamic_refs, token_budget, retrieval_query)`
- `ConsolidationJob(id, input_activity_refs, output_memory_refs, reviewer, status)`
- `PromptCacheProfile(id, provider, static_version, invalidation_reason, last_used_at)`

## Events

- `memory.item_created`
- `memory.consolidation_requested`
- `memory.consolidation_completed`
- `memory.fact_superseded`
- `memory.item_deprecated`
- `context.bundle_built`
- `prompt.static_section_invalidated`

## Contract Rules

- Every MemoryItem must declare its memory type: working, episodic, semantic, deprecated, or restricted.
- SemanticFacts must include evidence references and confidence.
- ContextBundles must list included dynamic references so prompt behavior can be audited.
- Prompt cache profiles must be versioned; any static section change invalidates the cache profile.
- Deprecated memory remains searchable but is excluded from default prompts.

## Weight Profile Contract

Memory retrieval, decay, and retention behavior must be controlled by versioned `WeightProfile` records or equivalent external configuration.

Recommended contract:

- `WeightProfile(id, tenant_id, domain, task_type, risk_level, version, feature_weights, thresholds, retention_overrides, owner, status)`

Contract rules:

- Feature weights must not be hard-coded in application logic.
- Profiles must be versioned and auditable.
- Different domains may use different profiles.
- Security, compliance, billing, production, and incident recovery memory may override ordinary decay.
- Profile changes must preserve old versions for audit and reproducibility.


## Question Intelligence Contracts

The memory layer must support repeated question detection, curiosity scoring, FAQ promotion, missing documentation discovery, and human correction through explicit contracts.

### QuestionObservation

Recommended contract:

    QuestionObservation:
        observation_id
        raw_question
        actor_ref
        actor_type
        tenant_id
        workspace_id
        project_id
        project_group_id
        task_ref
        session_ref
        source_surface
        detected_entities
        retrieval_result_summary
        answer_used_ref
        correction_ref
        created_at

Contract rules:

- Observations are append-only evidence.
- Observations must be scoped before normalization.
- Raw questions may require redaction before storage.
- Observations should preserve enough context to audit why a question was grouped.

### QuestionMemory

Recommended contract:

    QuestionMemory:
        question_id
        normalized_question
        question_intent
        scope
        tenant_id
        workspace_id
        project_id
        project_group_id
        related_symbols
        related_documents
        related_decisions
        related_tasks
        related_rules
        observation_count
        distinct_actor_count
        first_observed_at
        last_observed_at
        answer_status
        current_answer_ref
        evidence_refs
        curiosity_score
        faq_score
        urgency_score
        documentation_gap_score
        confidence_score
        freshness_score
        sensitivity_level
        owner
        next_action
        review_status
        lifecycle_state

Contract rules:

- QuestionMemory must be project-scoped by default.
- FAQ promotion must not change scope without authorization.
- Scores must be reproducible from a versioned scoring profile.
- Lifecycle state changes must emit events.
- Current answers must include evidence references and confidence.

### QuestionAnswer

Recommended contract:

    QuestionAnswer:
        answer_id
        question_id
        answer_text
        answer_type
        scope
        evidence_refs
        generated_by
        confidence_score
        freshness_status
        review_status
        reviewer_ref
        supersedes_answer_id
        correction_count
        reuse_count
        created_at
        updated_at

### KnowledgeGap

Recommended contract:

    KnowledgeGap:
        gap_id
        question_id
        gap_type
        missing_evidence
        affected_module
        affected_symbol
        impact
        owner
        recommended_action
        linked_task_id
        status
        created_at
        updated_at

### DocumentationDraft

Recommended contract:

    DocumentationDraft:
        draft_id
        question_id
        target_doc_ref
        target_symbol_ref
        draft_content
        evidence_refs
        confidence_score
        review_status
        owner
        created_task_id
        created_at
        updated_at

## Question Intelligence Events

Recommended events:

- question.observed
- question.normalized
- question.repetition_threshold_reached
- question.investigation_requested
- question.evidence_search_completed
- question.answer_candidate_created
- question.documentation_missing_detected
- question.documentation_draft_created
- question.knowledge_gap_created
- question.faq_candidate_created
- question.faq_promoted
- question.answer_corrected
- question.answer_superseded
- question.archived

Event rules:

- Every event must include tenant, workspace, project, and optional project group scope.
- Evidence search events must list searched source categories and omitted high-ranking evidence when relevant.
- FAQ promotion events must include scoring profile version and approval reference when required.
- Documentation draft events must include review requirement and owner.

## Question Intelligence Profile

Recommended contract:

    QuestionIntelligenceProfile:
        profile_id
        tenant_id
        workspace_id
        project_id
        version
        curiosity_weights
        faq_weights
        urgency_weights
        documentation_gap_weights
        thresholds
        investigation_budget
        promotion_policy
        review_policy
        owner
        status
        created_at
        updated_at

Contract rules:

- Curiosity, FAQ, urgency, and documentation gap scores must not be hard-coded.
- Threshold changes must be versioned.
- Old profile versions must remain available for audit.
- High-risk domains may require stricter review thresholds.

## Work Batch Contracts

The memory layer must support batching so small agent actions do not create noisy long-term memory, premature documentation, or fragmented code review.

### WorkBatch

Recommended contract:

    WorkBatch:
        batch_id
        tenant_id
        workspace_id
        project_id
        project_group_id
        actor_ref
        actor_type
        task_ref
        session_ref
        objective_summary
        batch_type
        lifecycle_state
        start_time
        last_activity_at
        end_time
        boundary_signals
        changed_files
        changed_symbols
        commands_run
        tests_run
        decisions_detected
        risks_detected
        memory_candidates
        documentation_candidates
        review_candidates
        consolidation_status
        review_status
        documentation_status
        evidence_refs
        readiness_score
        risk_score
        defer_policy_ref
        owner

Lifecycle states:

- open
- active
- waiting_for_quiet_period
- ready_for_consolidation
- consolidating
- waiting_for_review
- completed
- canceled
- failed

### DeferredAction

Recommended contract:

    DeferredAction:
        action_id
        batch_id
        action_type
        target_refs
        reason_for_deferral
        trigger_condition
        max_wait_until
        priority
        risk_level
        status
        owner
        created_at
        executed_at

Allowed action types:

- memory_consolidation
- documentation_generation
- code_review
- architecture_quality_scan
- impact_report
- task_decomposition
- faq_promotion
- long_term_memory_promotion

### BatchDecision

Recommended contract:

    BatchDecision:
        decision_id
        batch_id
        decision_source
        decision_type
        defer_or_execute
        confidence
        reason
        boundary_condition
        immediate_action_required
        scoring_profile_version
        created_at

### BatchPolicyProfile

Recommended contract:

    BatchPolicyProfile:
        profile_id
        tenant_id
        workspace_id
        project_id
        version
        readiness_weights
        immediate_action_rules
        quiet_period_rules
        max_batch_duration
        max_batch_size
        documentation_thresholds
        review_thresholds
        memory_thresholds
        owner
        status

Contract rules:

- Batching thresholds must be configurable and versioned.
- Raw events remain append-only even when long-term memory is deferred.
- Critical security, secret, destructive, or policy-blocking events bypass ordinary batching.
- A WorkBatch must preserve evidence references so deferred actions can run from final state.

## Work Batch Events

Recommended events:

- batch.opened
- batch.activity_recorded
- batch.boundary_signal_detected
- batch.deferred_action_created
- batch.ready_for_consolidation
- batch.consolidation_started
- batch.consolidation_completed
- batch.documentation_generation_requested
- batch.code_review_requested
- batch.immediate_action_triggered
- batch.completed
- batch.canceled
- batch.failed

## Feedback And Correction Contracts

The platform must support explicit user correction from the web interface. Corrections must be structured so they can affect memory confidence, retrieval feedback, rules, tasks, documentation drafts, and future agent behavior.

### FeedbackRecord

Recommended contract:

    FeedbackRecord:
        feedback_id
        tenant_id
        workspace_id
        project_id
        project_group_id
        target_type
        target_ref
        correction_type
        corrected_value
        reason
        created_by
        created_at
        affected_memory_refs
        affected_question_refs
        affected_rule_refs
        affected_task_refs
        affected_doc_refs
        status
        audit_ref

Allowed correction types:

- wrong_answer
- wrong_memory
- stale_memory
- wrong_scope
- wrong_task_decomposition
- wrong_rule_interpretation
- wrong_documentation_draft
- wrong_code_impact_analysis
- wrong_connector_mapping
- missing_context
- unsafe_action

Contract rules:

- FeedbackRecord must be scoped.
- Corrections must not mutate previous evidence destructively.
- Corrections should create audit events.
- Corrections may lower confidence, supersede memory, create Tasks, create Gaps, or request review.
- High-risk corrections require approval when they alter rules, security behavior, or shared memory.

## Feedback Events

Recommended events:

- feedback.created
- feedback.applied_to_memory
- feedback.applied_to_question_answer
- feedback.rule_improvement_suggested
- feedback.task_reopened
- feedback.gap_created
- feedback.review_requested
- feedback.rejected

Event rules:

- Every feedback event must include scope and target reference.
- Events that affect retrieval ranking must include old and new confidence signals.
- Events that affect rules must include rule version or suggested new version.

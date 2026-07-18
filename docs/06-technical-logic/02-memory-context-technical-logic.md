# Memory and Context Technical Logic

## Technical Goal

The Memory and Context layer transforms structured records into agent-usable context. Its technical responsibility is to decide what should be remembered, what should be forgotten by default, what should be retrieved, and how context should be packed into prompts without wasting tokens or injecting stale truth.

## Memory Type Classifier

Every candidate memory item is classified into one of these types:

- `WORKING`: temporary session context.
- `EPISODIC`: historical event or completed work.
- `SEMANTIC`: durable current truth or rule.
- `RESTRICTED`: sensitive memory requiring access control.
- `DEPRECATED`: no longer active but retained for audit.

Classifier input signals:

- source entity type,
- owner domain,
- evidence confidence,
- linked code existence,
- linked Decision status,
- sensitivity score,
- expected half-life,
- retrieval frequency.

Classification logic:

```text
if contains_secret or sensitive_customer_data:
    type = RESTRICTED
elif active_decision or current_architecture_fact:
    type = SEMANTIC
elif task_is_active:
    type = WORKING
elif event_is_completed:
    type = EPISODIC
elif linked_entity_is_deleted_or_superseded:
    type = DEPRECATED
```

## Consolidation Logic

Consolidation turns many low-level events into fewer high-value facts.

Inputs:

- Activities,
- WorkLogs,
- Decisions,
- Issues,
- Tasks,
- test results,
- docs drift findings,
- approvals.

Outputs:

- SemanticFacts,
- deprecated facts,
- unresolved knowledge gaps,
- prompt cache invalidation events.

Consolidation algorithm:

```text
collect events for time_window or completed_task
cluster events by affected_entity and intent
remove duplicate retries and failed intermediate attempts
extract final state and durable constraints
compare with existing SemanticFacts
create new facts or supersede old facts
mark source event references
emit memory.consolidation_completed
```

## Current State Resolution

The platform should resolve current state through active SemanticFacts and active Decisions.

Resolution priority:

1. Human-approved active Decision.
2. Verified deployment or merge state.
3. Latest completed Task with passing acceptance checks.
4. Consolidated WorkLog with evidence.
5. Low-confidence inferred fact.

If two facts conflict, the system should not choose randomly. It should create a conflict record or escalation.

## Retrieval Scoring

Context retrieval should rank candidate memory items by relevance, authority, freshness, and risk.

```text
score =
    semantic_similarity * 0.30 +
    graph_distance_score * 0.25 +
    authority_score * 0.20 +
    freshness_score * 0.10 +
    risk_relevance_score * 0.10 +
    usage_success_score * 0.05
```

Penalty factors:

- deprecated status,
- low confidence,
- access restriction,
- conflicting active fact,
- excessive token size,
- irrelevant domain.

## Graph-Aware Retrieval

Vector search alone is insufficient. The retriever should combine graph traversal and semantic search.

Retrieval flow:

1. Start from Task, Issue, code symbol, or policy subject.
2. Traverse graph edges to linked Decisions, Docs, Rules, owners, and previous Tasks.
3. Run semantic search for additional related MemoryItems.
4. Merge results and remove duplicates.
5. Apply access control.
6. Rank using retrieval score.
7. Summarize large documents when token budget is limited.

## Prompt Packing Logic

Prompt sections should be packed in this order:

1. Stable cached architecture and policy section.
2. Active current-state facts for the task domain.
3. Task instructions and acceptance criteria.
4. Relevant Decisions and Rules.
5. Relevant docs and code anchors.
6. Recent errors or command outputs.
7. Optional history only when requested or needed.

Token budget policy:

```text
reserve 25 percent for model output
reserve 15 percent for task instructions
reserve 25 percent for current state and rules
reserve 20 percent for code and docs
reserve 10 percent for recent evidence
reserve 5 percent for safety margin
```

## Prompt Cache Invalidation

Static prompt cache should invalidate only when stable content changes.

Invalidation triggers:

- organization policy update,
- global architecture update,
- active high-level Decision change,
- tenant security rule change,
- context schema version change.

Non-invalidation triggers:

- task-specific error output,
- local file snippet,
- single drift finding,
- temporary command output.

## Decay and Garbage Collection Logic

Decay should reduce default prompt noise without destroying audit history.

Decay score:

```text
decay_score =
    age_weight +
    missing_link_weight +
    superseded_weight +
    low_usage_weight +
    owner_deprecation_weight -
    compliance_retention_weight -
    security_importance_weight
```

Actions by score:

- low score: keep active.
- medium score: keep active but reduce retrieval priority.
- high score: mark deprecated and exclude from default prompts.
- restricted high score: archive with retention policy.

## ContextBundle Contract

A ContextBundle must include:

- task ID,
- retrieval query,
- included MemoryItem IDs,
- included Decision IDs,
- included Doc IDs,
- static prompt version,
- token budget,
- redaction status,
- omitted high-scoring items with reason.

## Failure Handling

- If retrieval confidence is low, ask for clarification or escalate rather than injecting weak context.
- If token budget is exceeded, summarize and preserve source references.
- If current-state facts conflict, block automatic context generation for high-risk tasks.
- If prompt cache version is unknown, rebuild static section and record invalidation.

## Configurable Memory Weighting Logic

Memory retrieval and decay must use configurable weighting profiles. The application logic may define feature names and scoring flow, but it must not hard-code final weights. Weights should be loaded from a versioned policy profile and selected by tenant, project, domain, task type, risk level, and agent role.

## Weight Profile Contract

A WeightProfile should include:

```text
WeightProfile:
    profile_id
    tenant_id
    domain
    task_type
    risk_level
    version
    feature_weights
    thresholds
    retention_overrides
    owner
    status
    created_at
    updated_at
```

Example feature names:

```text
recency
usage_frequency
successful_reuse
semantic_similarity
graph_distance
graph_centrality
evidence_strength
domain_criticality
human_verified
conflict_penalty
deprecation_penalty
restricted_access_penalty
incident_recovery_value
```

The values assigned to these features must come from the active WeightProfile, not from code constants.

## Profile Selection Logic

```text
select_weight_profile(request):
    candidates = profiles where tenant_id matches request.tenant_id
    candidates = filter by project_id if project profile exists
    candidates = filter by domain if domain profile exists
    candidates = filter by task_type if task profile exists
    candidates = filter by risk_level if risk-specific profile exists
    return highest_specificity_active_profile(candidates)
```

Specificity order:

1. tenant + project + domain + task_type + risk_level,
2. tenant + project + domain + task_type,
3. tenant + domain,
4. tenant default,
5. platform default.

## Weighted Retrieval Formula

The formula should be data-driven:

```text
score(memory_item, request, profile):
    features = extract_features(memory_item, request)
    total = 0
    for feature_name, feature_value in features:
        weight = profile.feature_weights.get(feature_name, 0)
        total += normalize(feature_value) * weight
    total -= apply_penalties(memory_item, request, profile)
    total += apply_boosts(memory_item, request, profile)
    return clamp(total, 0, 1)
```

The code can define `extract_features`, `normalize`, `apply_penalties`, and `apply_boosts`, but the numeric weight values and thresholds should be profile-driven.

## Forgotten Memory Classification Logic

A low-scoring memory item should not automatically be deleted. It should be classified.

```text
classify_low_visibility_memory(item):
    if linked_code_missing or superseded_by_active_decision:
        return OBSOLETE
    if domain_criticality_high or incident_recovery_value_high:
        return DORMANT_BUT_IMPORTANT
    if evidence_strength_high and graph_degree_low:
        return UNDER_LINKED
    if conflicts_with_active_fact:
        return CONFLICTING
    if evidence_strength_low and usage_frequency_low:
        return LOW_CONFIDENCE
    return LOW_PRIORITY
```

Actions:

- `OBSOLETE`: mark deprecated and exclude from default prompts.
- `DORMANT_BUT_IMPORTANT`: retain, lower default rank, boost for incident/security/recovery contexts.
- `UNDER_LINKED`: create graph repair or documentation linking Task.
- `CONFLICTING`: create review or supersession workflow.
- `LOW_CONFIDENCE`: keep out of default prompts unless explicitly requested.
- `LOW_PRIORITY`: keep searchable but low ranked.

## Dynamic Decay Formula

Decay should be profile-driven and multi-signal:

```text
decay_score(item, profile):
    features = {
        age,
        missing_link_strength,
        supersession_strength,
        low_usage_duration,
        owner_deprecation_signal,
        compliance_retention_need,
        security_importance,
        incident_recovery_value,
        human_verified
    }
    return weighted_sum(features, profile.decay_weights)
```

A high age value alone must never be enough to delete or hide critical memory.

## Feedback Loop

After an agent run, the system should record whether retrieved memory was useful.

Feedback sources:

- task completed successfully,
- agent cited the memory in final output,
- human reviewer accepted or rejected the result,
- generated code passed tests,
- policy violation was avoided,
- incident response used the memory.

This feedback updates `successful_reuse`, `usage_quality`, and future retrieval ranking. The feedback update should change memory metrics, not hard-coded weights.

## Guardrails

- Compliance and security retention rules override decay.
- Restricted memory cannot be boosted into unauthorized contexts.
- Conflicting memory cannot be injected as current truth.
- Low-confidence generated memory must not outrank human-approved Decisions.
- WeightProfile changes must be audited and versioned.
- Agents should be able to explain why a memory item was retrieved or excluded.


## Autonomous Question Intelligence Logic

The Memory and Context layer should include a Question Intelligence loop. This loop detects repeated questions, unanswered questions, missing documentation, and stale answers. It should decide whether to answer from existing evidence, investigate further, generate a documentation draft, create a Task, create a KnowledgeGap, or promote an answer to FAQ memory.

### Question Processing Pipeline

    on_question_asked(raw_question, actor, scope):
        scoped_question = apply_scope(raw_question, scope)
        observation = record_question_observation(scoped_question)
        normalized = normalize_question(scoped_question)
        question_memory = upsert_question_memory(normalized, observation)
        scores = compute_question_scores(question_memory)

        if scores.urgency_score >= immediate_threshold:
            request_investigation(question_memory)
        elif scores.curiosity_score >= curiosity_threshold:
            enqueue_investigation(question_memory)
        elif scores.faq_score >= faq_candidate_threshold and question_memory.has_stable_answer:
            create_faq_candidate(question_memory)
        else:
            keep_as_observed_or_candidate(question_memory)

### Evidence Search Logic

    investigate_question(question_memory):
        enforce_scope(question_memory.scope)
        evidence = []
        evidence += search_project_faq(question_memory)
        evidence += search_active_semantic_facts(question_memory)
        evidence += search_decisions(question_memory)
        evidence += search_docs_graph(question_memory)
        evidence += search_code_graph(question_memory)
        evidence += search_worklogs_issues_tasks(question_memory)
        evidence += search_rule_evaluations(question_memory)
        evidence += search_human_feedback(question_memory)

        scored_evidence = score_evidence(evidence)
        result = decide_question_outcome(question_memory, scored_evidence)
        persist_result(result)
        emit_question_events(result)

### Scope Enforcement

Question Intelligence must apply tenant, workspace, project, and project group scope before retrieval or scoring. The system must not retrieve broad memory and filter only after ranking.

## Batched Memory And Deferred Knowledge Logic

The Memory and Context layer should include a WorkBatch loop. This loop separates append-only raw evidence capture from durable knowledge actions such as memory consolidation, documentation generation, code review, FAQ promotion, and long-term memory promotion.

### Batch Processing Pipeline

    on_activity_recorded(activity):
        enforce_scope(activity.scope)
        record_raw_activity(activity)
        batch = find_or_create_work_batch(activity)
        attach_activity_to_batch(batch, activity)
        update_batch_candidates(batch, activity)
        decision = classify_batch_behavior(batch, activity)
        apply_batch_policy(batch, decision)
        persist_batch_decision(batch, decision)
        emit_batch_events(batch, decision)

### LLM Batch Classification

    classify_batch_behavior(batch, latest_activity):
        features = extract_batch_features(batch, latest_activity)
        llm_output = llm_classify(features)
        validated_output = validate_batch_decision_output(llm_output)
        return validated_output

The LLM output must include:

- batch_action.
- batch_type.
- defer_or_execute.
- deferred_actions.
- immediate_actions.
- boundary_condition.
- max_wait_time.
- confidence.
- risk_level.
- reason.
- evidence_refs.

### Policy-Constrained Decision Logic

    apply_batch_policy(batch, decision):
        if contains_secret_signal(batch):
            force_immediate_action(secret_detection)
        if destructive_action_requested(batch):
            force_immediate_action(approval_required)
        if authentication_or_authorization_changed(batch):
            force_immediate_action(security_review)
        if public_contract_changed(batch):
            create_deferred_action(documentation_generation)
            create_deferred_action(code_review)
        if decision.defer_or_execute == defer:
            create_deferred_actions(batch, decision)
        if readiness_score(batch) >= ready_threshold:
            mark_ready_for_consolidation(batch)

Policy can override the LLM recommendation. The LLM may recommend deferral, but policy determines whether deferral is allowed.

### Readiness Scoring Logic

    readiness_score(batch, profile):
        features = {
            time_since_last_edit,
            explicit_completion_signal,
            tests_finished,
            tests_passing,
            semantic_coherence,
            file_change_stability,
            risk_level,
            documentation_impact,
            code_graph_impact,
            user_instruction_strength,
            review_boundary_signal,
            max_duration_pressure
        }
        return weighted_sum(features, profile.readiness_weights)

Readiness score must include explanation. A batch should not move to ready_for_consolidation without a boundary signal or policy reason.

### Deferred Action Execution

    execute_deferred_actions(batch):
        if batch.lifecycle_state != ready_for_consolidation:
            return wait

        final_context = build_final_batch_context(batch)

        if has_deferred_action(batch, memory_consolidation):
            consolidate_memory_from_final_context(final_context)

        if has_deferred_action(batch, documentation_generation):
            generate_docs_from_final_graph_state(final_context)

        if has_deferred_action(batch, code_review):
            run_code_review_with_batch_context(final_context)

        if all_required_actions_complete(batch):
            mark_batch_completed(batch)

### Documentation Deferral Logic

    should_generate_docs_immediately(activity, batch):
        if activity_changes_public_contract:
            return true
        if activity_changes_security_or_compliance_behavior:
            return true
        if activity_changes_production_configuration:
            return true
        if user_explicitly_requested_docs:
            return true
        return false

If this function returns false, documentation generation should be represented as a DeferredAction or documentation candidate, not immediate output.

### Code Review Deferral Logic

    should_run_review_now(activity, batch):
        if high_risk_policy_triggered:
            return true
        if user_explicitly_requested_review:
            return true
        if pull_request_created:
            return true
        if task_completed and tests_finished:
            return true
        return false

### Failure Handling

- If batch state cannot be determined, create a conservative WorkBatch and defer non-critical durable actions.
- If batch exceeds maximum duration, create a consolidation Task or request user checkpoint.
- If deferred documentation generation fails, create a documentation Task with evidence references.
- If deferred review fails, create a review Task and preserve final batch context.
- If immediate policy action triggers, execute it even while the batch remains active.
- If a user forces consolidation, record the override and run with current evidence.

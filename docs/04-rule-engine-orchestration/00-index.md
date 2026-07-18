# 04 - Rule Engine and Orchestration Index

## Mission

Coordinate agents and humans through semantic policies, risk detection, escalation, dependency analysis, and task routing.

## Files

- `01-feature-specification.md` defines orchestration features and functional requirements.
- `02-high-level-design.md` defines actors, components, evaluation flow, integrations, and reliability requirements.
- `03-low-level-design.md` defines policy selection, deterministic checks, LLM judge constraints, risk aggregation, escalation, impact traversal, and task routing.
- `04-data-contracts-and-events.md` defines policies, evaluations, tickets, impact maps, and runbooks.
- `05-risks-challenges-and-acceptance.md` defines risks and acceptance criteria.
- `06-detailed-section-design.md` provides deep rationale, policy design, LLM judge behavior, escalation details, edge cases, and phase output.
- `07-custom-rule-authoring-and-suggestion-workflows.md` defines user-authored rules, domain-scoped rules, conversation-derived rule suggestions, **guided business and process intake**, **challenge-by-challenge rule discovery**, **LLM-managed rule authoring**, feature profile rules, rule lifecycle, conflict handling, and admin-console rule workflows.

## Features Covered

- Semantic Rules and LLM-as-a-Judge
- Escalation and Human-in-the-Loop
- Hybrid Anomaly Detection
- Dependency and Impact Analysis
- Domain-Scoped Feature Rules
- Conversation-Based Rule Suggestions
- Custom Rule Authoring
- Guided Rule Intake And Challenge Resolution
- LLM-Managed Rule Drafting

## Related Technical Logic

- `../06-technical-logic/04-rules-orchestration-technical-logic.md` explains policy evaluation, deterministic pre-checks, LLM judge constraints, escalation, impact traversal, and task routing.

## Related Customization Design

- `07-custom-rule-authoring-and-suggestion-workflows.md` should be read before implementing user rule editors, rule suggestions, domain packs, or feature profile rules.

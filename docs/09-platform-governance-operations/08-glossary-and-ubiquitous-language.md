# Glossary and Ubiquitous Language

## Purpose

AgentCore spans agents, memory, documentation, code graphs, rules, brokers, and operations. A shared vocabulary prevents ambiguity between engineering, product, security, and business teams.

## Terms

### Activity

An atomic record of an action performed by an agent or human.

### WorkLog

A session-level summary of attempted work, completed changes, blockers, and follow-ups.

### Decision

A record explaining why a technical or product choice was made.

### Issue

A discovered problem, risk, inconsistency, or need.

### Task

Executable work assigned to an agent or human.

### SemanticFact

A durable fact representing current project truth, architecture, rule, or domain knowledge.

### ContextBundle

The exact set of context prepared for an agent task, including references, static prompt version, and token budget.

### WeightProfile

A versioned configuration object that controls memory retrieval, decay, retention, and forgotten-memory handling.

### Code-Knowledge Graph

A graph representation of code files, classes, functions, methods, imports, calls, documentation, embeddings, and related decisions.

### GraphRetrievalProfile

A versioned configuration object that controls graph retrieval scoring, expansion, confidence thresholds, and penalties.

### DriftFinding

A record indicating documentation is missing, stale, invalid, or disconnected from code.

### RuleEvaluation

A record of a policy evaluation result, including verdict, confidence, rationale, and evidence.

### EscalationTicket

A human approval request created when automation reaches a risk boundary.

### Universal Agent JSON

The vendor-neutral structured message format used by agents, IDEs, adapters, and tools.

### DeadLetter

A broker message that failed delivery or validation and requires inspection or replay.

### Port Profile

A versioned or local configuration that assigns service ports for development or runtime environments.

## Naming Rules

- Use Activity for atomic actions.
- Use WorkLog for session summaries.
- Use Issue for discovered conditions.
- Use Task for executable work.
- Use Decision for rationale.
- Use DriftFinding for documentation synchronization problems.
- Use EscalationTicket for human approval workflows.

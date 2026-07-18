# Memory and Context - Risks, Challenges, and Acceptance

## Challenges

- Over-consolidation can erase important evidence.
- Old history can confuse agents if injected as current state.
- Prompt caching requires stable ordering and versioning; small unnecessary changes can destroy cache hit rates.
- RAG retrieval can miss critical rules unless graph links and semantic search are combined.
- Memory decay must be conservative for security, compliance, and architectural decisions.

## Mitigation Strategy

- Keep raw evidence reachable through artifact references.
- Separate current state from historical events in schema and retrieval logic.
- Version static prompt sections and track invalidation reasons.
- Combine vector search with graph traversal and policy filters.
- Require owner review for deprecating high-risk semantic facts.

## Acceptance Criteria

- Agents receive current state by default and historical events only when relevant.
- Stable architecture context is versioned and cacheable across tasks.
- Deleted or deprecated code causes linked memory to be marked deprecated and excluded from default prompts.
- A task can request additional context through a retrieval interface with traceable sources.

# Ingestion and Living Documentation Workflow

## Purpose

This workflow updates the Code-Knowledge Graph whenever code changes. It parses code, detects changed symbols, generates or refreshes documentation for changed nodes, and upserts nodes and relationships into Neo4j.

## Trigger Strategy

The system should not index on every file save by default. Save events are too noisy and often represent incomplete work.

Recommended triggers:

- Git commit.
- Pull request opened or updated.
- Manual sync button in an IDE.
- Scheduled repository scan.
- CI indexing job.
- Explicit agent request after code generation.

## Workflow Steps

### 1. Trigger

A repository event or manual sync starts the ingestion job. The job records repository path, commit hash, changed files, branch, actor, and correlation ID.

### 2. File Discovery

The system identifies supported source files and excludes generated files, vendor directories, build outputs, dependency folders, caches, and binary files.

### 3. Parsing (multi-language)

Python is the mandatory baseline language (`stdlib_ast`). TypeScript, JavaScript, Go, and Rust are supported through tree-sitter adapters registered in `code_graph_service.domain.parsers`.

Each file carries an explicit `language` (or is mapped from extension). Parsers emit a common `ParsedSymbol` schema without executing project code. Unsupported languages fail validation rather than writing incomplete nodes.


### 4. Symbol Extraction

The parser extracts code symbols and metadata:

- symbol kind,
- qualified name,
- signature,
- parameters,
- return type when available,
- body range,
- call expressions,
- imports,
- inheritance declarations.

### 5. Hash-Based Diffing

For every extracted symbol, the system computes a normalized hash and compares it to the hash stored in Neo4j.

Only changed or new symbols are sent to the AI documentation pipeline. Unchanged symbols are not reprocessed.

### 6. AI Documentation Generation

Changed symbols are sent to a low-cost model or local model first. The model generates documentation that includes:

- purpose,
- parameters,
- return value,
- side effects,
- dependencies,
- error behavior,
- usage notes,
- risk notes when relevant.

### 7. Embedding Generation

A compact semantic representation is embedded for vector search. The embedding should represent the symbol purpose and relationships, not just raw code text.

### 8. Graph Upsert

Neo4j is updated with new or changed nodes and relationships.

Upsert operations should be idempotent:

- merge Project node,
- merge File node,
- merge Class/Function/Method nodes,
- update hash and documentation,
- merge CONTAINS relationships,
- merge IMPORTS relationships,
- merge CALLS relationships,
- merge INHERITS_FROM relationships.

### 9. Drift and Impact Events

After graph update, the system emits events for Docs-as-Code and Orchestration:

- changed documented symbol,
- missing documentation,
- changed public API,
- changed dependency edge,
- changed call graph impact.

## Pseudo-Code

```text
ingest_repository_change(change_event):
    files = discover_supported_files(change_event)
    for file in files:
        ast = parse_with_tree_sitter(file)
        symbols = extract_symbols(ast)
        imports = extract_imports(ast)
        calls = extract_calls(ast)

        upsert_file_node(file)

        for symbol in symbols:
            new_hash = normalized_ast_hash(symbol)
            old_hash = graph.get_hash(symbol.identity)

            if old_hash != new_hash:
                doc = generate_ai_documentation(symbol)
                embedding = embed(symbol, doc)
                upsert_symbol(symbol, new_hash, doc, embedding)
            else:
                touch_symbol_index_metadata(symbol)

        upsert_relationships(file, symbols, imports, calls)
        emit_graph_delta_events(file)
```

## Documentation Quality Rules

Generated documentation should not be vague. It must include concrete information available from code and graph context.

Bad documentation:

```text
This function handles user data.
```

Better documentation:

```text
Loads a user record by ID, validates that the record exists, and returns a normalized user DTO. It depends on UserRepository.findById and throws NotFoundError when the user does not exist.
```

## Failure Handling

- If parsing fails, store an indexing failure and do not delete existing graph data.
- If AI documentation fails, upsert the symbol with `doc_status = PENDING`.
- If embedding fails, keep graph structure and schedule embedding retry.
- If relationship resolution is uncertain, store relationship with low confidence.
- If graph upsert fails, retry idempotently using the same correlation ID.

# Code-Knowledge Graph - Vision and Scope

## Vision

The Code-Knowledge Graph is a live structural memory of the codebase. It represents the project as a graph of files, classes, functions, methods, dependencies, calls, documentation, pgvector embedding references, and semantic relationships.

The purpose is to let AI understand and modify code with minimal hallucination, minimal token cost, and maximum awareness of existing project structure.

## Problem Statement

Traditional AI coding workflows often fail because the model sees either too little context or too much raw code. Too little context causes hallucinated functions and broken integration. Too much context causes high token cost, slow response, and confusion.

A graph-backed approach solves this by storing structured knowledge about the codebase and retrieving only the relevant nodes, relationships, signatures, documentation, and summaries needed for the current task.

## Product Goal

The system should support two major capabilities:

1. Living Documentation: when code changes, the graph and generated documentation update automatically.
2. Graph-Guided Code Generation: when a user asks for new code, the AI retrieves relevant graph context instead of reading the full repository.

## Difference from Simple Graphify-Style Systems

A basic code graph may show files and dependencies. AgentCore needs more than that. It needs a graph that supports AI workflows, documentation drift detection, code generation, token optimization, and enterprise governance.

The upgraded design includes:

- AST-based code parsing.
- Function-level hashing.
- AI-generated documentation stored per node.
- Embeddings stored in PostgreSQL pgvector for semantic search.
- Call graph and import graph relationships.
- Context retrieval for code generation.
- Tiered local/cloud model routing.
- Smart triggers to avoid unnecessary processing.
- Integration with AgentCore Decisions, Issues, Tasks, and Rules.

## Scope

In scope:

- File, Class, Function, Method, Import, and Module graph nodes.
- Neo4j graph schema with pgvector-backed semantic retrieval integration.
- Tree-sitter based parsing.
- Hash-based change detection.
- AI-generated documentation for changed symbols.
- Embeddings for semantic lookup.
- Graph-based retrieval for code generation.
- Token optimization strategies.

Out of scope for the initial implementation:

- Executing arbitrary project code during indexing.
- Replacing source control.
- Guaranteeing semantic correctness without tests.
- Fully automatic merge of generated code without review.

## Expected Benefits

### Living Documentation

Documentation stays attached to code symbols and updates when those symbols change.

### Lower Hallucination

The AI receives real existing signatures, documentation, and graph neighbors, reducing fake function calls and invented APIs.

### Lower Token Cost

The AI sees summaries and relevant graph context instead of entire source files.

### Impact Awareness

The graph shows which functions call each other, which files import each other, and which classes inherit from others.

### Enterprise Scalability

Hash-based diffing, local documentation models, cheap embeddings, and graph summaries make the approach viable for large repositories.

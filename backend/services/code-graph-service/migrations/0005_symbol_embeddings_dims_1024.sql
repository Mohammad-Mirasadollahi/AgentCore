-- Migrate symbol_embeddings from Phase-7 vector(16) to BGE-large 1024-d.
-- Idempotent: no-op when already vector(1024) or when the table is absent
-- (0003 creates it; Python ensure_schema also reconciles dims).

DO $$
DECLARE
    typ text;
BEGIN
    SELECT format_type(a.atttypid, a.atttypmod)
      INTO typ
      FROM pg_attribute a
      JOIN pg_class c ON c.oid = a.attrelid
      JOIN pg_namespace n ON n.oid = c.relnamespace
     WHERE n.nspname = 'code_graph'
       AND c.relname = 'symbol_embeddings'
       AND a.attname = 'embedding'
       AND a.attnum > 0
       AND NOT a.attisdropped;

    IF typ IS NULL OR typ = 'vector(1024)' THEN
        RETURN;
    END IF;

    DROP INDEX IF EXISTS code_graph.code_graph_symbol_embeddings_hnsw_idx;
    DROP INDEX IF EXISTS code_graph.code_graph_symbol_embeddings_scope_kind_idx;
    DROP INDEX IF EXISTS code_graph.code_graph_symbol_embeddings_scope_idx;
    DROP TABLE IF EXISTS code_graph.symbol_embeddings;

    CREATE TABLE code_graph.symbol_embeddings (
        symbol_id text PRIMARY KEY,
        tenant_id text NOT NULL,
        workspace_id text NOT NULL,
        project_id text NOT NULL,
        model text NOT NULL,
        dims integer NOT NULL CHECK (dims > 0),
        kind text NOT NULL DEFAULT 'unknown',
        embedding vector(1024) NOT NULL,
        updated_at timestamptz NOT NULL DEFAULT now()
    );

    CREATE INDEX code_graph_symbol_embeddings_scope_idx
        ON code_graph.symbol_embeddings (tenant_id, workspace_id, project_id);

    CREATE INDEX code_graph_symbol_embeddings_scope_kind_idx
        ON code_graph.symbol_embeddings (tenant_id, workspace_id, project_id, kind);

    CREATE INDEX code_graph_symbol_embeddings_hnsw_idx
        ON code_graph.symbol_embeddings
        USING hnsw (embedding vector_cosine_ops);
END $$;

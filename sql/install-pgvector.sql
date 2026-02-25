-- Install pgvector extension using pgxn
-- This requires network access during container initialization

-- Try installing via pgxn (if available)
DO $$
BEGIN
    PERFORM * FROM pg_extension WHERE extname = 'pgvector';
    IF NOT FOUND THEN
        -- Try loading the extension (might be pre-installed)
        CREATE EXTENSION IF NOT EXISTS vector;
    END IF;
END $$;

-- Alternative: Create tables without vector support if pgvector is not available
-- The system will work but with reduced similarity search capabilities

-- Add missing columns to emails table for LLM qualification
ALTER TABLE emails ADD COLUMN IF NOT EXISTS is_qualified BOOLEAN DEFAULT NULL;
ALTER TABLE emails ADD COLUMN IF NOT EXISTS qualification_stage VARCHAR DEFAULT NULL;
ALTER TABLE emails ADD COLUMN IF NOT EXISTS qualification_confidence FLOAT DEFAULT NULL;
ALTER TABLE emails ADD COLUMN IF NOT EXISTS qualification_reason TEXT DEFAULT NULL;
ALTER TABLE emails ADD COLUMN IF NOT EXISTS qualified_at TIMESTAMP DEFAULT NULL;

-- Add missing columns to documents table for processing metrics
ALTER TABLE documents ADD COLUMN IF NOT EXISTS page_count INTEGER DEFAULT 0;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS character_count INTEGER DEFAULT 0;

-- Verify the changes
\d emails;
\d documents;

-- Migration: Add Script and Character models
-- Date: 2026-05-12
-- Description: Restructure to support multiple scripts per project

-- Step 1: Create scripts table
CREATE TABLE IF NOT EXISTS scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    filename VARCHAR(255) NOT NULL,
    docx_path VARCHAR(500) NOT NULL,
    parsing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    parsing_progress INTEGER DEFAULT 0,
    parsing_total INTEGER DEFAULT 0,
    parsing_message VARCHAR(500),
    parsed_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_scripts_id ON scripts(id);
CREATE INDEX IF NOT EXISTS ix_scripts_project_id ON scripts(project_id);

-- Step 2: Create characters table
CREATE TABLE IF NOT EXISTS characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER NOT NULL,
    original_name VARCHAR(255) NOT NULL,
    alias_name VARCHAR(100),
    gender VARCHAR(20),
    description TEXT,
    has_reference_image BOOLEAN DEFAULT 0,
    reference_image_path VARCHAR(500),
    candidate_images_json JSON,
    user_asset_id INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_asset_id) REFERENCES user_assets(id)
);

CREATE INDEX IF NOT EXISTS ix_characters_id ON characters(id);
CREATE INDEX IF NOT EXISTS ix_characters_script_id ON characters(script_id);

-- Step 3: Migrate existing project data to scripts table
-- For each project with a docx_path, create a corresponding script record
INSERT INTO scripts (project_id, filename, docx_path, parsing_status, created_at, updated_at)
SELECT
    id as project_id,
    COALESCE(
        SUBSTR(docx_path, INSTR(docx_path, '/') + 1),
        'imported_script.docx'
    ) as filename,
    docx_path,
    CASE
        WHEN status = 'ready' THEN 'completed'
        WHEN status = 'parsing' THEN 'parsing'
        WHEN status = 'failed' THEN 'failed'
        ELSE 'pending'
    END as parsing_status,
    created_at,
    updated_at
FROM projects
WHERE docx_path IS NOT NULL AND docx_path != '';

-- Step 4: Add script_id to storyboard_segments table
-- First, add the column as nullable
ALTER TABLE storyboard_segments ADD COLUMN script_id INTEGER;

-- Update existing storyboard_segments to link to the newly created scripts
UPDATE storyboard_segments
SET script_id = (
    SELECT s.id
    FROM scripts s
    WHERE s.project_id = storyboard_segments.project_id
    LIMIT 1
)
WHERE script_id IS NULL;

-- Create index on script_id
CREATE INDEX IF NOT EXISTS ix_storyboard_segments_script_id ON storyboard_segments(script_id);

-- Step 5: Remove docx_path from projects table (optional - can be done later)
-- Note: SQLite doesn't support DROP COLUMN directly, so we'd need to recreate the table
-- For now, we'll leave it and just stop using it in the application

-- Verification queries (run these to check the migration)
-- SELECT COUNT(*) as script_count FROM scripts;
-- SELECT COUNT(*) as character_count FROM characters;
-- SELECT COUNT(*) as segments_with_script FROM storyboard_segments WHERE script_id IS NOT NULL;

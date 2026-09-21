-- Migration 003: Update storyboard_segments table to match model definition
-- Add missing columns for video generation workflow

-- Add video prompt columns
ALTER TABLE storyboard_segments ADD COLUMN video_prompt TEXT;
ALTER TABLE storyboard_segments ADD COLUMN video_prompt_edited TEXT;

-- Add generation progress and error columns
ALTER TABLE storyboard_segments ADD COLUMN generation_progress INTEGER DEFAULT 0;
ALTER TABLE storyboard_segments ADD COLUMN generation_error TEXT;

-- Add video thumbnail path (different from thumbnail_url)
ALTER TABLE storyboard_segments ADD COLUMN video_thumbnail_path VARCHAR(500);

-- Note: SQLite doesn't support renaming columns easily, so we keep both old and new columns
-- The application will use the new column names going forward

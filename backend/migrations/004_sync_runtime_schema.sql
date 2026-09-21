-- Migration: Sync runtime schema with current ORM models
-- Date: 2026-05-13
-- Description: Fix legacy SQLite schema drift for scripts/characters/costumes.

-- Normalize legacy script statuses so SQLAlchemy enum deserialization works.
UPDATE scripts SET parsing_status = 'PENDING' WHERE parsing_status = 'pending';
UPDATE scripts SET parsing_status = 'PARSING' WHERE parsing_status = 'parsing';
UPDATE scripts SET parsing_status = 'COMPLETED' WHERE parsing_status = 'completed';
UPDATE scripts SET parsing_status = 'FAILED' WHERE parsing_status = 'failed';

-- Bring characters table up to date with the ORM model.
ALTER TABLE characters ADD COLUMN reference_prompt TEXT;
ALTER TABLE characters ADD COLUMN generation_task_ids JSON;
ALTER TABLE characters ADD COLUMN generation_progress INTEGER DEFAULT 0;
ALTER TABLE characters ADD COLUMN generation_error TEXT;
ALTER TABLE characters ADD COLUMN selected_image_thumbnail VARCHAR(500);
ALTER TABLE characters ADD COLUMN first_appearance_segment INTEGER;
ALTER TABLE characters ADD COLUMN total_appearances INTEGER DEFAULT 0;

-- Bring costumes table up to date with the API/model contract.
ALTER TABLE costumes ADD COLUMN script_id INTEGER;
ALTER TABLE costumes ADD COLUMN candidate_images_json JSON;
ALTER TABLE costumes ADD COLUMN user_asset_id INTEGER;

CREATE INDEX IF NOT EXISTS ix_costumes_script_id ON costumes(script_id);

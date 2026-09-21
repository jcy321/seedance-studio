-- Migration: Add Asset and Generation Task models
-- Date: 2026-05-12
-- Description: Add Scene, Item, Costume, GenerationTask, and SegmentAsset models, and update Character and StoryboardSegment models

-- Step 1: Create scenes table
CREATE TABLE IF NOT EXISTS scenes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    reference_image_path VARCHAR(500),
    generation_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    generation_task_id INTEGER,
    candidate_images_json JSON,
    user_asset_id INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_asset_id) REFERENCES user_assets(id)
);

CREATE INDEX IF NOT EXISTS ix_scenes_id ON scenes(id);
CREATE INDEX IF NOT EXISTS ix_scenes_script_id ON scenes(script_id);

-- Step 2: Create items table
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    reference_image_path VARCHAR(500),
    generation_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    generation_task_id INTEGER,
    candidate_images_json JSON,
    user_asset_id INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_asset_id) REFERENCES user_assets(id)
);

CREATE INDEX IF NOT EXISTS ix_items_id ON items(id);
CREATE INDEX IF NOT EXISTS ix_items_script_id ON items(script_id);

-- Step 3: Create costumes table
CREATE TABLE IF NOT EXISTS costumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    script_id INTEGER NOT NULL,
    character_id INTEGER,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    reference_image_path VARCHAR(500),
    generation_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    generation_task_id INTEGER,
    candidate_images_json JSON,
    user_asset_id INTEGER,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (user_asset_id) REFERENCES user_assets(id)
);

CREATE INDEX IF NOT EXISTS ix_costumes_id ON costumes(id);
CREATE INDEX IF NOT EXISTS ix_costumes_script_id ON costumes(script_id);
CREATE INDEX IF NOT EXISTS ix_costumes_character_id ON costumes(character_id);

-- Step 4: Create generation_tasks table
CREATE TABLE IF NOT EXISTS generation_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress_percent INTEGER DEFAULT 0,
    prompt TEXT,
    result_url VARCHAR(500),
    error_message TEXT,
    metadata_json JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);

CREATE INDEX IF NOT EXISTS ix_generation_tasks_id ON generation_tasks(id);
CREATE INDEX IF NOT EXISTS ix_generation_tasks_status ON generation_tasks(status);
CREATE INDEX IF NOT EXISTS ix_generation_tasks_task_type ON generation_tasks(task_type);

-- Step 5: Create segment_assets table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS segment_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    segment_id INTEGER NOT NULL,
    asset_type VARCHAR(50) NOT NULL,
    asset_id INTEGER NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (segment_id) REFERENCES storyboard_segments(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_segment_assets_segment_id ON segment_assets(segment_id);
CREATE INDEX IF NOT EXISTS ix_segment_assets_asset_type_id ON segment_assets(asset_type, asset_id);

-- Step 6: Add generation fields to characters table
ALTER TABLE characters ADD COLUMN generation_status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE characters ADD COLUMN generation_task_id INTEGER;
ALTER TABLE characters ADD COLUMN selected_image_url VARCHAR(500);

-- Update existing characters to have 'pending' status
UPDATE characters SET generation_status = 'pending' WHERE generation_status IS NULL;

-- Step 7: Add generation fields to storyboard_segments table
ALTER TABLE storyboard_segments ADD COLUMN generation_task_id INTEGER;
ALTER TABLE storyboard_segments ADD COLUMN thumbnail_url VARCHAR(500);
ALTER TABLE storyboard_segments ADD COLUMN progress_percent INTEGER DEFAULT 0;
ALTER TABLE storyboard_segments ADD COLUMN video_generation_status VARCHAR(20) DEFAULT 'not_started';

-- Update existing segments to have 'not_started' status
UPDATE storyboard_segments SET video_generation_status = 'not_started' WHERE video_generation_status IS NULL;

-- Step 8: Add relationships between scripts and asset tables
-- (Already handled via script_id foreign keys in scenes, items, costumes tables)

-- Verification queries (run these to check the migration)
-- SELECT COUNT(*) as scene_count FROM scenes;
-- SELECT COUNT(*) as item_count FROM items;
-- SELECT COUNT(*) as costume_count FROM costumes;
-- SELECT COUNT(*) as generation_task_count FROM generation_tasks;
-- SELECT COUNT(*) as segment_asset_count FROM segment_assets;
-- SELECT COUNT(*) as characters_with_status FROM characters WHERE generation_status IS NOT NULL;
-- SELECT COUNT(*) as segments_with_status FROM storyboard_segments WHERE video_generation_status IS NOT NULL;

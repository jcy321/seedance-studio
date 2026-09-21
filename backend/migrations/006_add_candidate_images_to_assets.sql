-- Migration 006: Add candidate_images_json to scenes and items
-- Date: 2026-05-14
-- Description: Add candidate_images_json field to scenes and items tables for multi-image selection

-- Add candidate_images_json to scenes table
ALTER TABLE scenes ADD COLUMN candidate_images_json JSON;

-- Add candidate_images_json to items table
ALTER TABLE items ADD COLUMN candidate_images_json JSON;

-- Note: costumes table already has this field

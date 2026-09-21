-- Migration 005: Add user_asset_relations table
-- 用于记录资产之间的关系，特别是服装与角色的从属关系

CREATE TABLE IF NOT EXISTS user_asset_relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    from_asset_id INTEGER NOT NULL,
    to_asset_id INTEGER NOT NULL,
    relation_type VARCHAR(50) NOT NULL,
    source_project_id INTEGER,
    source_script_id INTEGER,
    metadata_json JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (from_asset_id) REFERENCES user_assets(id) ON DELETE CASCADE,
    FOREIGN KEY (to_asset_id) REFERENCES user_assets(id) ON DELETE CASCADE,
    FOREIGN KEY (source_project_id) REFERENCES projects(id) ON DELETE SET NULL,
    FOREIGN KEY (source_script_id) REFERENCES scripts(id) ON DELETE SET NULL
);

-- 创建唯一索引，避免重复关系
CREATE UNIQUE INDEX IF NOT EXISTS idx_user_asset_relations_unique
ON user_asset_relations(user_id, from_asset_id, to_asset_id, relation_type);

-- 创建查询索引
CREATE INDEX IF NOT EXISTS idx_user_asset_relations_from
ON user_asset_relations(from_asset_id);

CREATE INDEX IF NOT EXISTS idx_user_asset_relations_to
ON user_asset_relations(to_asset_id);

CREATE INDEX IF NOT EXISTS idx_user_asset_relations_user
ON user_asset_relations(user_id);

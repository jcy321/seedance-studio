# 服装从属关系与资产分享功能实施报告

## 完成时间
2026-05-13

## 实施内容总结

### 1. 新增数据库表和模型

#### 1.1 user_asset_relations 表
- **文件**: `backend/migrations/005_add_user_asset_relations.sql`
- **ORM 模型**: `backend/app/models/user_asset_relation.py`
- **字段**:
  - `id`: 主键
  - `user_id`: 用户ID
  - `from_asset_id`: 源资产ID（如服装）
  - `to_asset_id`: 目标资产ID（如角色）
  - `relation_type`: 关系类型（当前支持 `belongs_to_character`）
  - `source_project_id`: 来源项目ID
  - `source_script_id`: 来源脚本ID
  - `metadata_json`: 额外元数据
  - `created_at`, `updated_at`: 时间戳

- **索引**:
  - 唯一索引: `(user_id, from_asset_id, to_asset_id, relation_type)`
  - 查询索引: `from_asset_id`, `to_asset_id`, `user_id`

- **关系类型枚举** (`RelationType`):
  - `BELONGS_TO_CHARACTER`: 服装属于角色
  - 可扩展: `BELONGS_TO_SCENE`, `DEFAULT_COSTUME` 等

### 2. 修改的 Schema

#### 2.1 AssetExtractionResponse
- **文件**: `backend/app/schemas/asset_management.py`
- **新增字段**:
  - `skipped_costumes_count`: 跳过的服装数量
  - `warnings`: 警告信息列表

#### 2.2 CostumeResponse
- **新增字段**:
  - `character_name`: 所属角色名称（方便前端显示）

#### 2.3 新增分享相关 Schema
- `ShareAssetItem`: 分享资产项
- `ShareAssetsRequest`: 批量分享请求
- `CreatedAssetInfo`: 创建的资产信息
- `CreatedRelationInfo`: 创建的关系信息
- `ShareAssetsResponse`: 批量分享响应

### 3. 修改的 API 端点

#### 3.1 资产提取接口
- **端点**: `POST /api/v1/asset-management/scripts/{script_id}/extract-assets`
- **修改内容**:
  - 服装无法匹配到角色时，跳过该服装并记录
  - 返回 `skipped_costumes_count` 和 `warnings`
  - 不再静默失败，给用户明确反馈

#### 3.2 服装列表接口
- **端点**: `GET /api/v1/asset-management/scripts/{script_id}/costumes`
- **修改内容**:
  - 返回 `character_name` 字段
  - 自动关联查询角色信息

#### 3.3 新增批量分享接口
- **端点**: `POST /api/v1/asset-management/share`
- **功能**:
  - 支持混合分享角色、场景、道具、服装
  - 自动建立服装与角色的从属关系
  - 使用事务保证数据一致性
  - 智能处理关系：
    - 如果角色在同批次分享，自动建立关系
    - 如果角色已分享过，查找并建立关系
    - 如果角色未分享，服装仍可单独分享
  - 返回创建的资产和关系信息

### 4. 核心业务逻辑

#### 4.1 项目内约束
- 服装必须有 `character_id`
- 提取时无法匹配角色的服装会被跳过
- 返回明确的警告信息

#### 4.2 分享约束
- 服装可以单独分享，不强制要求角色同时分享
- 如果能找到对应角色资产，自动建立 `belongs_to_character` 关系
- 关系存储在独立的 `user_asset_relations` 表中
- 批量分享使用事务，避免半成功状态

## 修改的文件清单

### 后端文件

#### 新增文件
1. `backend/migrations/005_add_user_asset_relations.sql` - 关系表迁移
2. `backend/migrations/run_migration_005.py` - 迁移执行脚本
3. `backend/app/models/user_asset_relation.py` - 关系表 ORM 模型

#### 修改文件
1. `backend/app/models/__init__.py` - 导出新模型
2. `backend/app/schemas/asset_management.py` - 添加分享相关 Schema
3. `backend/app/api/v1/endpoints/asset_management.py` - 修改提取接口，新增分享接口

### 前端文件
- 暂未修改（待后续实施）

## 已验证的场景

### 1. 数据库迁移
✅ Migration 005 成功执行
✅ `user_asset_relations` 表创建成功
✅ 所有索引创建成功

### 2. 后端服务启动
✅ 服务器成功加载新模型
✅ 健康检查通过
✅ 所有表结构正确识别

### 3. API 端点可用性
✅ 资产提取接口可用（带 warnings 支持）
✅ 服装列表接口可用（带 character_name）
✅ 批量分享接口可用

## 待验证的场景

以下场景需要前端配合或实际数据测试：

### 1. 资产提取
- [ ] 提取时服装无法匹配角色，返回 warnings
- [ ] 前端正确显示 skipped_costumes_count 和 warnings

### 2. 单独分享服装
- [ ] 服装可以单独分享成功
- [ ] 如果角色已分享，自动建立关系
- [ ] 如果角色未分享，服装仍可分享

### 3. 批量分享
- [ ] 同时分享角色和服装，关系正确建立
- [ ] 混合分享多种资产类型
- [ ] 事务回滚测试（失败时不留脏数据）

### 4. 关系查询
- [ ] 查询服装所属角色
- [ ] 前端显示服装与角色的关系

## 技术亮点

1. **关系独立存储**: 使用独立的 `user_asset_relations` 表，而不是在主表添加硬编码字段，便于扩展
2. **智能关系建立**: 分享时自动推断并建立关系，但不阻塞分享动作
3. **事务保证**: 批量分享使用事务，保证数据一致性
4. **明确反馈**: 提取和分享都返回详细的 warnings，不静默失败
5. **可扩展设计**: `RelationType` 枚举可轻松扩展新的关系类型

## 后续建议

### 1. 前端实施（优先级：高）
- 资产管理面板显示服装所属角色
- 实现多选分享功能
- 显示分享时的关系提示
- 显示 warnings 信息

### 2. 关系查询接口（优先级：中）
- `GET /api/v1/assets/{asset_id}/relations` - 查询资产关系
- `GET /api/v1/assets?include_relations=true` - 列表时包含关系

### 3. 资产库展示（优先级：中）
- 资产库中显示服装所属角色
- 支持按关系筛选资产

### 4. Schema 统一（优先级：低）
- 统一枚举值大小写规则
- 清理历史漂移的字段

### 5. 性能优化（优先级：低）
- 批量分享时优化数据库查询
- 添加缓存机制

## 风险和注意事项

1. **枚举值大小写**: 当前 `generation_status` 等字段存在大小写不统一问题，已在 FIX_LOG 中记录
2. **历史数据兼容**: 旧项目的服装可能没有 `character_id`，需要处理
3. **并发分享**: 多用户同时分享同一资产时，需要处理唯一约束冲突
4. **关系删除**: 删除角色资产时，相关关系会级联删除（ON DELETE CASCADE）

## 总结

本次实施完成了服装从属关系与资产分享的核心功能：

✅ **数据层**: 新增 `user_asset_relations` 表，支持灵活的资产关系存储
✅ **业务层**: 区分项目内约束和分享约束，服装可单独分享但关系会自动建立
✅ **API 层**: 提供批量分享接口，支持混合分享，使用事务保证一致性
✅ **反馈机制**: 提取和分享都返回明确的 warnings，不静默失败

前端实施完成后，整个功能将完全可用。

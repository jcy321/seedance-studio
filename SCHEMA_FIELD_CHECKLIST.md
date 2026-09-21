# Schema 字段完整性检查清单

## 检查日期：2026-05-14

## 检查项目

### 1. 角色 (Character)

#### 数据库模型 (`app/models/character.py`)
- ✅ `reference_prompt` (Text) - 提示词字段
- ✅ `generation_status` (Enum) - 生成状态
- ✅ `description` (Text) - 描述

#### Response Schema (`app/schemas/character.py`)
- ✅ `CharacterResponse.reference_prompt` (Optional[str])
- ✅ `CharacterResponse.generation_status` (str)
- ✅ `CharacterResponse.description` (Optional[str])
- ✅ `CharacterListItem.reference_prompt` (Optional[str])
- ✅ `CharacterListItem.generation_status` (str)
- ✅ `CharacterListItem.description` (Optional[str])

#### API 端点 (`app/api/v1/endpoints/characters.py`)
- ✅ `/scripts/{script_id}/list` - 返回完整字段

---

### 2. 场景 (Scene)

#### 数据库模型 (`app/models/scene.py`)
- ✅ `image_prompt` (Text) - 提示词字段
- ✅ `generation_status` (Enum) - 生成状态
- ✅ `description` (Text) - 描述

#### Response Schema (`app/schemas/asset_management.py`)
- ✅ `SceneResponse.image_prompt` (Optional[str])
- ✅ `SceneResponse.generation_status` (str)
- ✅ `SceneResponse.description` (Optional[str])

#### API 端点 (`app/api/v1/endpoints/asset_management.py`)
- ✅ `/scripts/{script_id}/scenes` - 返回完整字段

---

### 3. 道具 (Item)

#### 数据库模型 (`app/models/item.py`)
- ✅ `image_prompt` (Text) - 提示词字段
- ✅ `generation_status` (Enum) - 生成状态
- ✅ `description` (Text) - 描述

#### Response Schema (`app/schemas/asset_management.py`)
- ✅ `ItemResponse.image_prompt` (Optional[str])
- ✅ `ItemResponse.generation_status` (str)
- ✅ `ItemResponse.description` (Optional[str])

#### API 端点 (`app/api/v1/endpoints/asset_management.py`)
- ✅ `/scripts/{script_id}/items` - 返回完整字段

---

### 4. 服装 (Costume)

#### 数据库模型 (`app/models/costume.py`)
- ✅ `image_prompt` (Text) - 提示词字段
- ✅ `generation_status` (Enum) - 生成状态
- ✅ `description` (Text) - 描述

#### Response Schema (`app/schemas/asset_management.py`)
- ✅ `CostumeResponse.image_prompt` (Optional[str])
- ✅ `CostumeResponse.generation_status` (str)
- ✅ `CostumeResponse.description` (Optional[str])
- ✅ `CostumeResponse.character_name` (Optional[str]) - 所属角色

#### API 端点 (`app/api/v1/endpoints/asset_management.py`)
- ✅ `/scripts/{script_id}/costumes` - 返回完整字段，包括角色名称

---

## 提示词生成接口

### 统一端点 (`/asset-management/generate-prompt`)
- ✅ 接收参数：`asset_type`, `asset_id`, `asset_name`, `asset_description`
- ✅ 保存逻辑：
  - 角色 → `reference_prompt`
  - 场景 → `image_prompt`
  - 道具 → `image_prompt`
  - 服装 → `image_prompt`

---

## 字段命名差异说明

### 为什么角色使用 `reference_prompt` 而其他使用 `image_prompt`？

**历史原因**：角色模型最早设计时使用了 `reference_prompt` 命名，表示"人设参考图提示词"。后续添加的场景、道具、服装统一使用了 `image_prompt` 命名。

**当前状态**：
- 后端代码已经正确处理这个差异
- 前端代码统一使用 `image_prompt` 或 `reference_prompt` 字段名
- API 响应中字段名保持一致

**是否需要统一**：
- 短期：不需要，当前实现已经正确处理
- 长期：可以考虑通过 migration 统一为 `image_prompt`

---

## 前端字段映射

### AssetWorkflowView 组件
- 角色：使用 `character.reference_prompt`
- 场景：使用 `scene.image_prompt`
- 道具：使用 `item.image_prompt`
- 服装：使用 `costume.image_prompt`

---

## 验证步骤

1. ✅ 检查所有数据库模型字段
2. ✅ 检查所有 Response Schema 字段
3. ✅ 检查所有 API 端点返回值
4. ✅ 检查提示词生成接口保存逻辑
5. ⏳ 前端测试：生成提示词后是否显示内容和按钮

---

## 结论

所有后端 Schema 和 API 端点都已正确配置，包含必要的字段：
- `description` - 资产描述
- `image_prompt` / `reference_prompt` - 图像提示词
- `generation_status` - 生成状态

前端应该能够正确显示这些字段。如果仍然有问题，需要检查：
1. 前端 API 调用是否正确
2. 前端数据绑定是否正确
3. 浏览器控制台是否有错误

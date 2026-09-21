# Seedance Studio 项目进度记录

## 项目概述

**项目名称**：Seedance Studio - AI 驱动的动画制作工作流系统

**技术栈**：
- 前端：原生 HTML/CSS/JavaScript (Babel + React JSX)
- 后端：Python FastAPI + SQLAlchemy
- 数据库：SQLite
- AI 服务：火山方舟 API (豆包大模型)

**核心功能**：
1. 剧本上传与解析（DOCX 格式）
2. 分镜自动拆解
3. 资产提取（角色、场景、道具、服装）
4. AI 生成提示词
5. AI 生成设计图
6. 资产管理与分享

---

## 当前状态（2026-05-14）

### ✅ 已完成功能

#### 1. 核心数据模型
- ✅ User（用户）
- ✅ Project（项目）
- ✅ Script（剧本）
- ✅ StoryboardSegment（分镜片段）
- ✅ Character（角色）
- ✅ Scene（场景）
- ✅ Item（道具）
- ✅ Costume（服装）
- ✅ GenerationTask（生成任务）
- ✅ UserAsset（用户资产库）
- ✅ UserAssetRelation（资产关系表）

#### 2. 数据库迁移
- ✅ Migration 001: 初始化用户和项目表
- ✅ Migration 002: 添加剧本和分镜表
- ✅ Migration 003: 添加角色和资产表
- ✅ Migration 004: 添加生成任务和用户资产表
- ✅ Migration 005: 添加资产关系表

#### 3. 后端 API 端点

**用户认证** (`/api/v1/auth`)
- ✅ POST `/register` - 用户注册
- ✅ POST `/login` - 用户登录
- ✅ GET `/me` - 获取当前用户信息

**项目管理** (`/api/v1/projects`)
- ✅ POST `/` - 创建项目
- ✅ GET `/` - 获取项目列表
- ✅ GET `/{id}` - 获取项目详情
- ✅ PUT `/{id}` - 更新项目
- ✅ DELETE `/{id}` - 删除项目

**剧本管理** (`/api/v1/scripts`)
- ✅ POST `/projects/{project_id}/upload` - 上传剧本
- ✅ GET `/{script_id}` - 获取剧本详情
- ✅ GET `/{script_id}/parsing-progress` - 获取解析进度
- ✅ GET `/{script_id}/segments` - 获取分镜列表

**角色管理** (`/api/v1/characters`)
- ✅ GET `/scripts/{script_id}/list` - 获取角色列表
- ✅ GET `/{character_id}` - 获取角色详情
- ✅ POST `/{character_id}/generate-images` - 生成角色图像
- ✅ POST `/{character_id}/select-image` - 选择角色图像

**资产管理** (`/api/v1/asset-management`)
- ✅ POST `/scripts/{script_id}/extract-assets` - 提取资产
- ✅ GET `/scripts/{script_id}/scenes` - 获取场景列表
- ✅ GET `/scripts/{script_id}/items` - 获取道具列表
- ✅ GET `/scripts/{script_id}/costumes` - 获取服装列表
- ✅ POST `/generate-prompt` - 生成资产提示词
- ✅ POST `/share` - 批量分享资产到资产库

**生成任务** (`/api/v1/generation`)
- ✅ GET `/tasks` - 获取生成任务列表
- ✅ GET `/tasks/{task_id}` - 获取任务详情
- ✅ POST `/tasks/{task_id}/poll` - 轮询任务状态

#### 4. 前端页面

**主要视图**
- ✅ LoginView - 登录页面
- ✅ RegisterView - 注册页面
- ✅ ProjectListView - 项目列表
- ✅ ProjectDetailView - 项目详情
- ✅ ScriptDetailView - 剧本详情（分镜列表）
- ✅ AssetWorkflowView - 资产管理工作流（新增）

**AssetWorkflowView 功能**
- ✅ 四个标签页：角色、场景、道具、服装
- ✅ 统计信息：总计、已完成、生成中、失败
- ✅ 资产卡片展示：名称、描述、状态、提示词
- ✅ 生成提示词功能
- ✅ 生成图像功能
- ✅ 服装显示所属角色
- ✅ 多选分享功能

#### 5. 核心服务

**LLM 服务** (`app/services/llm_service.py`)
- ✅ 调用火山方舟 API
- ✅ 支持流式和非流式响应
- ✅ 错误处理和重试机制

**资产提取服务** (`app/services/asset_extraction_service.py`)
- ✅ 从分镜中提取角色、场景、道具、服装
- ✅ 生成资产提示词
- ✅ 处理服装与角色的关联关系
- ✅ 返回警告信息（无法匹配角色的服装）

**图像生成服务** (`app/services/image_generation_service.py`)
- ✅ 调用火山方舟图像生成 API
- ✅ 创建和管理生成任务
- ✅ 轮询任务状态
- ✅ 下载和保存生成的图像

---

## 最近修复的问题

### 2026-05-14 修复记录

#### 问题 1：前端 API 路径错误
**现象**：点击"开始提取"报错"请先上传剧本"，但数据库中已有 25 个分镜

**根因**：前端 API 路径与后端路由不匹配
- 前端调用：`/scripts/${scriptId}/extract-assets`
- 后端实际：`/asset-management/scripts/${scriptId}/extract-assets`

**修复**：系统性修正所有前端 API 路径
- 资产提取：添加 `/asset-management` 前缀
- 资产列表：角色使用 `/characters` 前缀，其他使用 `/asset-management` 前缀
- 提示词生成：统一使用 `/asset-management/generate-prompt`

#### 问题 2：前端 JavaScript 语法错误
**现象**：浏览器黑屏，控制台报 Babel 语法错误

**根因**：
1. 重复的代码块（第 585-603 行）
2. `toast` 函数调用缺少空格（`toast(...)`写成了`toast(...)`）

**修复**：删除重复代码，修正函数调用语法

#### 问题 3：生成提示词后没有显示内容和按钮
**现象**：点击"生成提示词"后，界面没有显示提示词内容和"生成图像"按钮

**根因**：`CharacterResponse` 和 `CharacterListItem` Schema 缺少必要字段
- 缺少 `reference_prompt` 字段
- 缺少 `generation_status` 字段
- 缺少 `description` 字段

**修复**：更新 Schema 添加缺失字段

#### 问题 4：角色生成提示词后仍无"生成图像"按钮
**现象**：在资产管理页面，点击角色卡的"生成提示词"，提示"提示词已生成"后，依旧没有出现"生成图像"按钮

**根因**：前端字段名不一致问题
- 角色使用 `reference_prompt` 字段存储提示词
- 场景、道具、服装使用 `image_prompt` 字段存储提示词
- 前端只检查 `asset.image_prompt`，导致角色的 `reference_prompt` 无法被识别

**修复位置**：`/root/seedance-studio/frontend/index.html`
1. **提示词显示**（第1877行、第2322行）：
   - 修改前：`{asset.image_prompt && (`
   - 修改后：`{(asset.image_prompt || asset.reference_prompt) && (`
   
2. **生成提示词按钮显示条件**（第1888行、第2330行）：
   - 修改前：`{!asset.image_prompt && (`
   - 修改后：`{!(asset.image_prompt || asset.reference_prompt) && (`
   
3. **生成图像按钮显示条件**（第1896行、第2337行）：
   - 修改前：`{asset.image_prompt && asset.generation_status !== 'completed' && (`
   - 修改后：`{(asset.image_prompt || asset.reference_prompt) && asset.generation_status !== 'completed' && (`
   
4. **生成图像API调用**（第1693行、第2044行）：
   - 修改前：`prompt: asset.image_prompt || asset.description`
   - 修改后：`prompt: asset.image_prompt || asset.reference_prompt || asset.description`

**影响范围**：
- AssetWorkflowView 组件（资产工作流页面）
- AssetManagementPanel 组件（资产管理面板）

---

## 核心设计决策

### 1. 服装从属关系设计

**需求**：
- 服装必须从属于角色
- 资产分享时可以忽略从属关系（单独分享服装）

**实现方案**：
- `costumes` 表有 `character_id` 外键（必填）
- `user_asset_relations` 表记录资产库中的关系
- 分享时：
  - 如果只分享服装，不创建关系记录
  - 如果同时分享角色和服装，创建 `costume_belongs_to_character` 关系

### 2. 字段命名差异

**现状**：
- 角色使用 `reference_prompt` 字段（历史原因）
- 场景、道具、服装使用 `image_prompt` 字段

**处理方式**：
- 后端代码正确处理这个差异
- 提示词生成接口根据资产类型保存到不同字段
- 前端根据资产类型读取对应字段

**未来优化**：可以考虑通过 migration 统一为 `image_prompt`

### 3. 资产管理工作流

**设计理念**：参考火山引擎界面，集中处理所有资产操作

**流程**：
1. 上传剧本 → 自动拆解分镜
2. 点击"管理资产" → 进入资产工作流页面
3. 提取资产 → 显示所有资产
4. 生成提示词 → 为每个资产生成图像描述
5. 生成图像 → 调用 AI 生成设计图
6. 选择图像 → 确定最终使用的图像
7. 分享到资产库 → 供其他项目复用

---

## 待完成功能

### 高优先级

1. **图像生成后的选择功能**
   - 显示 4 张候选图的缩略图
   - 支持选择其中一张作为最终图像
   - 更新资产状态为"已完成"

2. **资产库管理页面**
   - 查看所有已分享的资产
   - 搜索和筛选资产
   - 在新项目中引用资产

3. **分镜与资产关联**
   - 为每个分镜选择使用的角色、场景、道具、服装
   - 显示分镜预览（文字描述 + 资产缩略图）

### 中优先级

4. **批量操作优化**
   - 批量生成提示词
   - 批量生成图像
   - 批量选择图像

5. **生成任务管理**
   - 显示所有生成任务的进度
   - 支持取消正在进行的任务
   - 失败任务的重试功能

6. **用户配置管理**
   - 在前端页面配置火山方舟 API 密钥
   - 配置默认生成参数（图像尺寸、数量等）

### 低优先级

7. **导出功能**
   - 导出项目数据（JSON 格式）
   - 导出分镜脚本（PDF 格式）
   - 导出资产清单（Excel 格式）

8. **协作功能**
   - 项目成员管理
   - 权限控制
   - 评论和反馈

---

## 技术债务

### 需要重构的部分

1. **前端架构**
   - 当前使用原生 JavaScript + Babel，代码较为混乱
   - 建议迁移到 React + TypeScript
   - 引入状态管理（Redux 或 Zustand）

2. **API 路径规范**
   - 当前路径不够统一（`/characters` vs `/asset-management`）
   - 建议统一为 `/api/v1/assets/{type}` 格式

3. **错误处理**
   - 前端错误处理不够完善
   - 需要统一的错误提示组件
   - 需要更详细的错误日志

4. **测试覆盖**
   - 缺少单元测试
   - 缺少集成测试
   - 需要添加 E2E 测试

### 性能优化

1. **数据库查询优化**
   - 添加必要的索引
   - 优化 N+1 查询问题
   - 考虑引入缓存（Redis）

2. **图像处理优化**
   - 生成缩略图时使用异步任务
   - 考虑使用 CDN 存储图像
   - 实现图像懒加载

3. **前端性能**
   - 实现虚拟滚动（资产列表）
   - 优化大文件上传（分片上传）
   - 添加加载状态和骨架屏

---

## 开发环境

### 后端启动
```bash
cd /root/seedance-studio/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端访问
```
http://localhost:8000/
```

### 数据库位置
```
/root/seedance-studio/backend/seedance.db
```

### 日志位置
```
/tmp/backend.log
```

---

## 数据库 Schema 说明

### 核心表关系

```
users (用户)
  └── projects (项目)
        └── scripts (剧本)
              ├── storyboard_segments (分镜片段)
              ├── characters (角色)
              ├── scenes (场景)
              ├── items (道具)
              └── costumes (服装)
                    └── character_id (外键到 characters)

user_assets (用户资产库)
  └── user_asset_relations (资产关系)
        ├── from_asset_id (外键到 user_assets)
        └── to_asset_id (外键到 user_assets)

generation_tasks (生成任务)
  ├── 关联到 characters
  ├── 关联到 scenes
  ├── 关联到 items
  └── 关联到 costumes
```

### 重要字段说明

**generation_status 枚举值**：
- `pending` - 待生成
- `generating` - 生成中
- `completed` - 已完成
- `failed` - 失败

**asset_type 枚举值**：
- `character` - 角色
- `scene` - 场景
- `item` - 道具
- `costume` - 服装

**relation_type 枚举值**：
- `costume_belongs_to_character` - 服装从属于角色

---

## 常见问题排查

### 1. 后端启动失败
- 检查 Python 版本（需要 3.8+）
- 检查依赖是否安装：`pip install -r requirements.txt`
- 检查端口 8000 是否被占用：`lsof -i :8000`

### 2. 前端页面空白
- 检查浏览器控制台错误
- 检查后端服务是否运行
- 检查 `/tmp/backend.log` 日志

### 3. API 调用失败
- 检查 API 路径是否正确
- 检查请求头是否包含 `Authorization: Bearer <token>`
- 检查后端日志中的错误信息

### 4. 图像生成失败
- 检查火山方舟 API 配置是否正确
- 检查 API 密钥是否有效
- 检查网络连接是否正常
- 查看 `generation_tasks` 表中的 `error_message` 字段

---

## 参考文档

### 项目内文档
- `API_FIXES.md` - API 修复记录
- `IMPLEMENTATION_REPORT_2026-05-13.md` - 实施报告
- `CLOTHING_RELATION_AND_SHARING_SPEC.md` - 服装关系和分享规范
- `SCHEMA_FIELD_CHECKLIST.md` - Schema 字段检查清单
- `FIX_LOG_2026-05-13.md` - 修复日志
- `CLAUDE_HANDOFF_PROMPT.md` - Claude 交接文档

### 外部文档
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 文档](https://docs.sqlalchemy.org/)
- [火山方舟 API 文档](https://www.volcengine.com/docs/82379)

---

## 下一步计划

### 短期目标（1-2 周）
1. 完成图像选择功能
2. 完成资产库管理页面
3. 完成分镜与资产关联功能
4. 添加基础的单元测试

### 中期目标（1-2 月）
1. 前端迁移到 React + TypeScript
2. 添加用户配置管理页面
3. 优化性能和用户体验
4. 完善错误处理和日志

### 长期目标（3-6 月）
1. 添加协作功能
2. 实现导出功能
3. 支持更多文件格式
4. 移动端适配

---

## 团队协作说明

### 代码提交规范
- 使用语义化提交信息（Conventional Commits）
- 每个功能使用独立分支开发
- 提交前运行代码格式化和 lint 检查

### 分支管理
- `main` - 主分支，保持稳定
- `develop` - 开发分支
- `feature/*` - 功能分支
- `bugfix/*` - 修复分支

### Code Review 要点
- 检查代码风格和规范
- 检查错误处理是否完善
- 检查是否有安全隐患
- 检查是否有性能问题
- 检查是否有测试覆盖

---

**最后更新时间**：2026-05-14 08:00 UTC
**更新人**：Claude (Kiro)
**项目状态**：开发中 🚧

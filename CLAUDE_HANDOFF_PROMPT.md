# Claude 交接 Prompt

你现在接手 `/root/seedance-studio` 项目，请直接在代码库内完成以下工作，不要只做分析。

## 必读上下文

先阅读这两份文档：

1. `/root/seedance-studio/FIX_LOG_2026-05-13.md`
2. `/root/seedance-studio/CLOTHING_RELATION_AND_SHARING_SPEC.md`

其中：
- `FIX_LOG_2026-05-13.md` 记录了已经做过的热修、已直接改动的 SQLite、以及还没清完的技术债。
- `CLOTHING_RELATION_AND_SHARING_SPEC.md` 是这次你要继续实现的目标方案。

## 你的目标

请把“服装必须从属于角色”和“资产分享时可以忽略这种从属关系而单独分享”这两个要求同时落地。

核心要求：

1. 在项目内数据语义上：
   - `costume` 必须能关联到 `character`
   - 如果服装无法匹配角色，不应创建这条服装
   - 但接口要返回 warning / skipped 信息，不能静默吞掉

2. 在资产库分享语义上：
   - 服装可以单独分享
   - 不要求用户必须先分享对应角色
   - 如果对应角色也已分享，则要保留“服装属于角色”的关系

3. 在数据建模上：
   - 不要把“服装属于角色”的关系硬编码塞进 `user_assets`
   - 请新增独立关系表，例如 `user_asset_relations`

## 具体任务

### A. 统一并修复 schema / migration

请先做一次 schema 对账：

- 对照 `backend/app/models/*.py`
- 对照当前 SQLite 实际表结构
- 清理本项目目前 ORM 与 SQLite 历史漂移问题

至少覆盖这些表：
- `scripts`
- `characters`
- `scenes`
- `items`
- `costumes`
- `storyboard_segments`
- `user_assets`

要求：
- 新增正式 migration
- 不要依赖临时热修维持正确性
- 枚举值大小写规则要统一

### B. 新增资产关系表

请新增表，建议命名：
- `user_asset_relations`

建议字段：
- `id`
- `user_id`
- `from_asset_id`
- `to_asset_id`
- `relation_type`
- `source_project_id`
- `source_script_id`
- `metadata_json`
- `created_at`
- `updated_at`

先至少支持一种关系类型：
- `belongs_to_character`

并加唯一约束，避免重复关系。

### C. 调整资产提取接口

修改：
- `POST /api/v1/asset-management/scripts/{script_id}/extract-assets`

要求：
- 若服装无法匹配到角色，则不要写入该服装
- 返回结构中增加：
  - `skipped_costumes_count`
  - `warnings`

不要再用“静默 continue 但用户无感知”的方式结束。

### D. 实现资产分享

请新增批量分享接口，建议：
- `POST /api/v1/asset-management/share`

支持混合分享：
- character
- scene
- item
- costume

行为要求：

1. 分享单件服装：
   - 允许成功
   - 如果已能找到对应角色资产，则补关系
   - 如果找不到角色资产，也不能失败

2. 同批次分享角色 + 服装：
   - 自动建立 `belongs_to_character`

3. 多选分享时：
   - 整个分享过程放进事务
   - 不允许留下半成功脏数据

### E. 前端最小接入

请至少完成最小前端支持：

- 资产管理面板中，服装项能显示“所属角色”
- 分享时支持多选
- 分享服装时如果存在所属角色，给出非阻塞提示：
  - 例如“该服装属于角色 X，一起分享可自动保留关系”

不要求你把 UI 做得很重，但要完整可用。

## 需要特别注意

1. 你不是从零开始，这个项目已经被热修过一轮，不要把已有修复回退掉。
2. 当前库是 SQLite，迁移方案请考虑 SQLite 限制。
3. 不要把“项目内约束”和“分享约束”混为一个判断。
4. 如果你发现现有 API / schema 名称不统一，可以顺手统一，但要保证前后端一起改通。

## 验收标准

完成后请你自己验证以下场景：

1. 资产提取时，服装若找不到角色，不会 500，但会在响应中告诉前端被跳过了。
2. 用户可单独分享一件服装，不报错。
3. 用户同时分享角色和其服装时，关系会被记录。
4. 资产库里可以查到“这件服装属于哪个角色”。
5. 多选分享支持角色、场景、道具、服装混选。
6. ORM、migration、SQLite 实际表结构一致，不再靠热修兜底。

## 输出要求

完成后请给出：

1. 你修改了哪些文件
2. 你新增了哪些 migration
3. 你验证了哪些场景
4. 还剩哪些风险或后续建议


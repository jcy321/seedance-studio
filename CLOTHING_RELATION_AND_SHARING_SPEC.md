# 服装从属关系与资产分享实现说明

本文档是给 Claude 的实现说明，目标是把“服装必须属于角色”和“分享资产时可以忽略这种从属关系”这两件事同时成立。

## 1. 业务目标

用户要求：

- 在剧本/提取语义上：
  - 服装必须有从属角色。
  - 场景、物品可以没有从属角色。
- 在资产分享/入库语义上：
  - 用户分享服装时，不应被这个从属关系阻塞。
  - 可以单独分享一件服装。
  - 也可以多选多个资产一起分享。
  - 分享后如果能保留“这件服装原本属于哪个角色”的关系最好，但不能因此阻止分享动作。

换句话说，要区分两层语义：

1. 项目内生产语义：
   - 服装必须挂在角色下。
2. 资产库分享语义：
   - 资产可独立分享，但关系应尽量保留为元数据。

## 2. 当前现状

### 2.1 项目内数据层

当前项目内已有的服装归属关系：
- `costumes.character_id`

这已经表达了“服装从属于角色”。

### 2.2 资产库层

当前资产库只有一张泛化表：
- `user_assets`

当前字段只能表达：
- 资产类型
- 名称
- 描述
- 图片
- 来源项目

不能表达：
- 某件服装属于哪个角色资产
- 某个资产和另一个资产之间的关系

### 2.3 当前问题

如果直接把 `Costume` 分享成 `user_assets`：
- 服装本身可以入库
- 但“属于哪个角色”会丢失

如果强行要求“必须先分享角色才能分享服装”：
- 会破坏你要的 UX

所以需要一套“关系可记录，但不阻塞分享”的设计。

## 3. 推荐设计

## 3.1 核心原则

- 服装在项目内必须有角色归属。
- 资产入库时，服装本体和“归属关系”分开保存。
- 分享动作永远以“资产本体”优先，不因关系缺失而失败。
- 如果能推断出角色关系，就额外写入关系记录。

## 3.2 不推荐方案

不建议直接在 `user_assets` 上新增一个硬编码字段：
- `owner_character_asset_id`

原因：
- 只适合“服装 -> 角色”这一种关系
- 后续如果还想支持“道具属于场景”“角色有默认服装”等，会继续堆字段
- 扩展性差

## 3.3 推荐方案：新增资产关系表

新增表：
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

建议语义：

- `from_asset_id`
  - 发起关系的资产
  - 这里通常是“服装资产”
- `to_asset_id`
  - 被指向的资产
  - 这里通常是“角色资产”
- `relation_type`
  - 先至少支持：
    - `belongs_to_character`

建议唯一索引：
- `(user_id, from_asset_id, to_asset_id, relation_type)`

这样可避免重复写入同一条关系。

## 3.4 为什么这个方案最合适

它能同时满足：

- 服装可以独立存在于资产库
- 服装与角色的归属关系可单独保存
- 单独分享服装时，不强制角色资产也同时存在
- 多选分享时，如果角色一起分享，可立即建立关系
- 后续扩展别的资产关系时，不用再改主表

## 4. 具体行为定义

## 4.1 项目内提取

规则：
- `costumes.character_id` 必须有值
- 如果 LLM 产出的服装无法匹配到角色：
  - 不创建这条服装
  - 记录 `skipped_costumes`
  - 在接口响应里返回跳过数量和原因

不建议继续使用“静默跳过且无反馈”的方式。

建议把 `AssetExtractionResponse` 扩展为：
- `characters_count`
- `scenes_count`
- `items_count`
- `costumes_count`
- `skipped_costumes_count`
- `warnings: List[str]`

## 4.2 分享单件服装

允许。

处理逻辑：
- 先创建服装资产到 `user_assets`
- 尝试推断所属角色：
  - 如果该服装源 `costume.character_id` 对应的角色已经存在资产库映射，则创建 `user_asset_relations`
  - 如果不存在映射，则只分享服装本体，不报错

也就是说：
- “关系尽量补”
- “没有关系也不阻塞分享”

## 4.3 同时分享角色和服装

允许。

处理逻辑：
- 同一批次里先创建角色资产
- 再创建服装资产
- 再创建 `belongs_to_character` 关系

这是最完整的分享路径。

## 4.4 多选分享

允许：
- 角色 + 服装
- 只有服装
- 只有角色
- 场景/道具/服装混选

批量分享应放在一个事务里。

推荐顺序：
1. 先按类型分组
2. 先创建角色资产
3. 再创建服装资产
4. 最后批量写关系表

## 5. 需要新增的数据映射

当前项目表到资产库表之间，还缺一层“已分享映射”。

建议至少补齐以下映射能力：

- `characters.user_asset_id`
- `scenes.user_asset_id`
- `items.user_asset_id`
- `costumes.user_asset_id`

其中：
- `characters.user_asset_id`
  - 当前代码里已有字段
- `scenes.user_asset_id`
  - 模型已有
- `items.user_asset_id`
  - 模型已有
- `costumes.user_asset_id`
  - 这次热修已给 SQLite 补列，但仍需把完整业务流接上

用途：
- 知道项目内某条资产是否已经分享过
- 知道服装所属角色是否已有对应用户资产
- 建关系时不需要反复按名字猜

## 6. API 层建议

## 6.1 分享接口

建议不要只做单条分享，直接补一套批量接口。

推荐新增：
- `POST /asset-management/share`

请求体建议：

```json
{
  "project_id": 5,
  "items": [
    {"asset_type": "character", "source_id": 12},
    {"asset_type": "costume", "source_id": 23},
    {"asset_type": "scene", "source_id": 8}
  ]
}
```

返回值建议：

```json
{
  "created_assets": [
    {"asset_type": "character", "source_id": 12, "user_asset_id": 101},
    {"asset_type": "costume", "source_id": 23, "user_asset_id": 102}
  ],
  "created_relations": [
    {
      "relation_type": "belongs_to_character",
      "from_asset_id": 102,
      "to_asset_id": 101
    }
  ],
  "warnings": []
}
```

## 6.2 查询关系

推荐新增：
- `GET /assets/{asset_id}/relations`

或者：
- `GET /assets?include_relations=true`

至少要让前端能展示：
- 这件服装属于哪个角色

## 7. 前端交互建议

## 7.1 项目资产管理面板

服装列表里建议直接展示：
- 服装名
- 所属角色
- 是否已分享

这样用户一眼知道关系是否完整。

## 7.2 分享弹窗

建议行为：

- 多选列表里，服装项旁显示所属角色名
- 用户勾选服装时：
  - 不强制自动勾选角色
  - 但可以提示：
    - “该服装属于角色 X，一起分享可自动保留关系”

这符合你的要求：
- 不阻塞分享
- 但鼓励完整分享

## 7.3 资产库展示

在资产库里：
- 服装卡片可显示“所属角色：xxx”
- 但这个关系只是展示/筛选增强，不影响资产本体独立存在

## 8. 建议实现顺序

给 Claude 的推荐顺序：

1. 先整理并统一 `characters / costumes / user_assets` 的字段与迁移
2. 新增 `user_asset_relations` 表及 migration
3. 补批量分享接口
4. 在分享逻辑里写入 `costumes.user_asset_id` / `characters.user_asset_id`
5. 前端补“多选分享”和“所属角色展示”
6. 最后把“提取资产接口的 warnings/skipped_count”补齐

## 9. Claude 实现时必须注意的点

### 9.1 不要再把“项目内约束”和“分享约束”混成一个判断

正确拆分：
- 项目内：
  - 服装必须属于角色
- 分享时：
  - 服装可以单独分享
  - 关系有则保存，无则不阻塞

### 9.2 关系应落独立表，不要把主表继续做成万能垃圾桶

原因：
- 后面一定会继续长出别的资产关系

### 9.3 批量分享要用事务

否则会出现：
- 角色资产成功
- 服装资产成功
- 关系写失败

最后数据半成功，用户很难理解。

## 10. 最终验收标准

Claude 做完后，至少要满足以下场景：

1. 提取出的服装一定能对应到某个角色，否则接口返回 warning，不创建该服装
2. 用户可单独分享一件服装，不报错
3. 用户可同时分享角色和其服装，关系被保留
4. 资产库中可看到“服装属于哪个角色”
5. 多选分享支持角色、场景、道具、服装混选
6. 批量分享失败时不会留下半套脏数据


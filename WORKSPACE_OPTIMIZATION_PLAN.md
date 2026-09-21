# 工作区逻辑优化方案

## 概述

本文档整理了对剧本工作区的优化建议。**核心前提**：用户上传的docx文件已包含完整的分镜表格（镜号、景别、镜头内容、台词、时长、转场、摄像机运动等），LLM的作用是**解析分镜表格并生成适合火山方舟API的提示词**，而不是将剧本转换为分镜。

请在相应章节批注您的想法和需求。

---

## 1. 分镜表格解析流程

### 1.1 docx分镜表格结构

**实际表格列：**
- 镜号
- 是否多镜头
- 景别（全景/特写/近景/侧景等）
- **镜头内容**（包含场景、角色、道具、动作描述）
- 台词
- 单位时长
- 转场方式
- 摄像机运动方式
- 摄像机运动控制（camera_control JSON）
- 备注（音效）

**示例数据：**
```
镜号: 1
景别: 全景
镜头内容: 星核主控室，全息屏幕滚动数据流，林野穿银色维护服敲击键盘，屏幕显示星禾情感阈值12%
台词: 林野（低声）：妈妈，你到底在哪里？
单位时长: 0:10
摄像机运动控制: {"object":"","type":"camera","config":{"horizontal":0,"vertical":0,"pan":0,"tilt":0,"roll":0,"zoom":5}}
```

### 1.2 解析流程优化（分步骤）

**优化后流程：**
```
步骤1：上传docx → 解析表格 → 创建StoryboardSegment记录
       ↓
步骤2：LLM提取资产 → 生成资产提示词
       ↓
步骤3：用户管理资产（生成图片或选择复用）
       ↓
步骤4：LLM生成视频提示词（基于已有资产）
       ↓
步骤5：用户选择分镜生成视频
```

**步骤2：LLM提取资产和生成提示词**

这是第一个关键步骤，LLM的作用：
1. **从"镜头内容"中提取结构化信息**
2. **识别角色、场景、道具、服装**
3. **为每个资产生成专用提示词**（用于生成人设图/场景图/物品图）

**重要**：只有完成步骤2和步骤3（资产准备完成）后，才能进入步骤4生成视频提示词。

**步骤4：LLM生成视频提示词**

基于已准备好的资产，LLM为每个分镜生成视频提示词：
- 引用已生成的角色人设图
- 引用场景图（如果有）
- 结合分镜表格中的镜头信息
- 生成完整的视频生成提示词

### 1.3 LLM解析输出结构

**步骤2输出：资产提取和提示词生成**

**输入：** 分镜表格的"镜头内容"字段
```
星核主控室，全息屏幕滚动数据流，林野穿银色维护服敲击键盘，屏幕显示星禾情感阈值12%
```

**LLM输出（步骤2）：**
```json
{
  "segment_id": 1,
  "scene": {
    "name": "星核主控室",
    "type": "室内",
    "description": "科技感主控室，全息屏幕滚动数据流",
    "image_prompt": "A futuristic control room with holographic screens displaying data streams, high-tech interior, sci-fi style, cinematic lighting, 4K"
  },
  "characters": [
    {
      "name": "林野",
      "appearance": "穿银色维护服",
      "action": "敲击键盘",
      "reference_prompt": "A young person wearing silver maintenance uniform, short hair, focused expression, sci-fi character design, full body reference sheet, multiple angles"
    }
  ],
  "items": [
    {
      "name": "全息屏幕",
      "description": "显示星禾情感阈值12%的全息屏幕",
      "image_prompt": "Holographic screen displaying emotional threshold data, futuristic UI design, glowing blue interface"
    },
    {
      "name": "银色维护服",
      "type": "costume",
      "description": "科技感银色维护服",
      "image_prompt": "Silver maintenance uniform, sci-fi style, futuristic workwear"
    }
  ]
}
```

**步骤4输出：视频提示词生成**

在用户完成资产准备（生成图片或选择复用）后，LLM生成视频提示词：

```json
{
  "segment_id": 1,
  "video_prompt": "Wide shot of futuristic control room, holographic screens with data streams, character Lin Ye in silver maintenance uniform typing on keyboard, screen shows emotional threshold 12%, cinematic sci-fi atmosphere, cold lighting",
  "camera_info": {
    "shot_type": "全景",
    "movement": "固定镜头，轻微变焦",
    "camera_control": {"horizontal":0,"vertical":0,"pan":0,"tilt":0,"roll":0,"zoom":5}
  },
  "referenced_assets": {
    "character_images": ["林野人设图URL"],
    "scene_images": ["星核主控室场景图URL"],
    "item_images": []
  }
}
```

**关键点：**
- 步骤2：提取资产，生成资产图提示词
- 步骤3：用户生成资产图或选择复用
- 步骤4：基于已有资产，生成视频提示词
- 视频提示词会引用已生成的资产图

### 1.4 LLM优化分镜（可选功能，下一步）

**功能说明：**
虽然docx已包含完整分镜表格，但可以让用户选择是否让LLM综合优化分镜。

**优化方向：**
1. **风格统一**
   - 用户选择风格：写实、动漫、科幻、奇幻等
   - LLM根据风格调整所有分镜的描述和提示词

2. **镜头优化**
   - 优化镜头衔接和转场
   - 建议更合适的景别和运镜
   - 优化节奏和时长分配

3. **叙事优化**
   - 分析情节连贯性
   - 建议增删分镜
   - 优化情绪曲线

**使用场景：**
```
用户上传分镜表格 → 选择"让LLM优化分镜" → 选择风格 → LLM生成优化建议 → 用户确认 → 应用优化
```

**优先级：** P2（增强功能）

---

## 2. 资产管理系统

### 2.1 资产提取和管理

**从分镜表格中提取的资产类型：**
1. **角色（Character）**
   - 从"镜头内容"中识别角色名称
   - 提取角色外观描述（服装、动作）
   - 生成角色人设图提示词
   
2. **场景（Scene/Location）**
   - 识别场景名称和类型（室内/室外）
   - 提取场景描述
   - 生成场景参考图提示词

3. **道具/物品（Item）**
   - 识别重要道具（全息屏幕、照片、数据终端等）
   - 提取物品描述
   - 生成物品参考图提示词

4. **服装（Costume）**
   - 识别角色服装（银色维护服等）
   - 关联到角色
   - 支持同一角色多套服装

### 2.2 角色管理功能

**核心需求：**
1. **解析完成后显示全部角色**
   - 自动从所有分镜中提取角色列表
   - 显示角色名称、出场次数、外观描述
   - 状态标识：✅已生成人设图 / ⏳未生成 / 🔗已关联资产库

2. **筛选功能**
   - 全部角色
   - 已生成人设图的角色
   - 未生成人设图的角色

3. **单独为角色生成人设图**
   - 点击角色卡片 → 查看LLM生成的提示词
   - 用户可编辑提示词
   - 调用火山方舟API生成4张候选图
   - 选择一张作为最终人设图

4. **批量生成**
   - 选择多个未生成的角色
   - 批量调用API生成人设图
   - 显示生成进度

5. **资产库复用**
   - 从个人资产库选择已有角色
   - 直接应用到当前脚本的角色

### 2.3 场景管理

**功能：**
- 显示所有场景列表（星核主控室、意识对接舱等）
- 为场景生成参考图（可选，用于保持一致性）
- 场景复用：从资产库选择已有场景

### 2.4 道具/物品管理

**功能：**
- 显示所有道具列表
- 为重要道具生成参考图（如照片、数据终端）
- 道具库管理

### 2.5 服装管理

**功能：**
- 识别角色的不同服装（银色维护服、便装等）
- 同一角色可以有多套服装
- 在分镜中选择角色使用哪套服装

---

## 3. 提示词编辑和管理

### 3.1 提示词的两个层次

#### 层次1：资产提示词（Asset Prompt）
用于生成角色人设图、场景图、物品图的提示词。

**特点：**
- 独立于具体分镜
- 用于生成可复用的参考图
- 需要多角度、完整的描述

**示例（角色人设图）：**
```
A young person wearing silver maintenance uniform, short hair, focused expression, 
sci-fi character design, full body reference sheet, multiple angles, 
character turnaround, clean background, high quality
```

#### 层次2：分镜视频提示词（Video Prompt）
用于生成具体分镜视频的提示词。

**特点：**
- 包含场景、角色、动作、镜头信息
- 结合表格中的景别、摄像机运动等参数
- 需要描述具体的动作和情节

**示例（分镜1视频）：**
```
Wide shot of futuristic control room, holographic screens with data streams, 
character Lin Ye in silver maintenance uniform typing on keyboard, 
screen shows emotional threshold 12%, cinematic sci-fi atmosphere, 
cold lighting, camera: fixed with slight zoom
```

### 3.2 提示词编辑器功能

**基础功能：**
1. **查看LLM生成的提示词**
   - 解析完成后，每个资产和分镜都有LLM生成的初始提示词
   - 用户可以查看和编辑

2. **编辑提示词**
   - 支持富文本编辑
   - 实时字数统计
   - 提示词长度建议

3. **提示词模板**
   - 预设模板：人物特写、全景、动作场景等
   - 用户自定义模板
   - 快速应用模板

**增强功能：**
1. **资产引用**
   - 在分镜视频提示词中引用已生成的资产
   - 语法：`@角色名`、`#场景名`、`$道具名`
   - 自动替换为资产的描述

2. **一致性检查**
   - 检测同一角色在不同分镜中的描述是否一致
   - 高亮不一致的地方
   - 提供统一修改功能

3. **提示词预览**
   - 显示最终生成的完整提示词
   - 显示引用的资产缩略图

### 3.3 提示词生成策略

**资产提示词生成：**
```
LLM从"镜头内容"提取 → 生成英文提示词 → 用户可编辑 → 调用API生成图片
```

**视频提示词生成：**
```
基础描述 + 场景 + 角色+动作 + 道具 + 镜头信息 + 用户补充
```

**示例组合：**
```
[景别] Wide shot
[场景] futuristic control room with holographic screens
[角色] Lin Ye in silver maintenance uniform typing on keyboard
[道具] screen displays emotional threshold 12%
[氛围] cinematic sci-fi atmosphere, cold lighting
[镜头] camera: fixed with slight zoom (zoom:5)
```

---

## 4. 分镜选择和生成工作流

### 4.1 分镜列表展示

**显示信息：**
- 镜号
- 景别
- 镜头内容（简要）
- 时长
- 状态：✅已生成 / ⏳待生成 / ⚠️缺少资产
- 预览缩略图（已生成的）

### 4.2 选择性生成

**核心需求：**
1. **多选分镜**
   - 每行分镜前有复选框
   - 支持单选、多选、全选、反选
   - 支持范围选择（如1-10镜）

2. **生成按钮**
   - 显示已选择的分镜数量
   - 预估生成时间和成本
   - 点击后开始生成

**UI示例：**
```
[全选] [反选] [范围选择: 1-10]

☑ 镜1 | 全景 | 星核主控室，林野敲击键盘... | 0:10 | ⏳待生成
☑ 镜2 | 特写 | 林野口袋里的照片... | 0:09 | ⏳待生成
☐ 镜3 | 侧景 | 陈默走进主控室... | 0:10 | ⚠️缺少陈默人设图

[生成选中的分镜 (2个) | 预估时间: 约5分钟]
```

### 4.3 生成前检查

**自动检查项：**
1. ✓ 分镜涉及的角色是否都有人设图
2. ✓ 视频提示词是否完整
3. ✓ 火山方舟API配置是否正确
4. ⚠️ 场景是否有参考图（可选，不阻塞）

**检查结果展示：**
```
生成前检查：
✓ 2个角色已生成人设图
⚠️ 1个角色(陈默)缺少人设图 - 建议先生成
✓ 所有视频提示词已完善
✓ API配置正常

[继续生成] [取消] [先生成缺失的人设图]
```

### 4.4 生成进度和任务管理

**核心需求：**
1. **任务状态追踪**
   - 每个生成任务（资产图/视频）都有唯一任务ID
   - 状态：排队中 → 生成中 → 已完成 / 失败
   - 支持自动轮询和手动刷新

2. **视频生成进度查询**
   - 调用火山方舟API后获得任务ID
   - 轮询查询任务进度：
   ```json
   {
     "query": {
       "id": "cgt-20260511202118-w8rxk"
     },
     "body": {}
   }
   ```
   - 返回进度百分比和状态

3. **图片生成状态管理**
   - 虽然火山方舟生图API可能没有任务查询接口
   - 前端需要显示"生成中"状态
   - 使用loading动画或进度条
   - 生成完成后显示缩略图

**UI展示要求：**

**资产图生成UI/UX：**
```
角色：林野

[转圈loading] [转圈loading] [转圈loading] [转圈loading]
   生成中...      生成中...      生成中...      生成中...

↓ 完成后 ↓

[缩略图1] [缩略图2] [缩略图3] [缩略图4]

点击任意缩略图 → 弹窗显示原图 → 可选择该图作为人设图
```

**具体交互：**
1. 点击"生成人设图"按钮
2. 立即显示4个转圈loading UI（表示生成中）
3. 后台轮询任务状态
4. 每张图生成完成后，转圈UI替换为缩略图
5. 点击缩略图 → 弹窗查看原图 → 点击"选择此图"按钮

**视频生成UI/UX：**
```
分镜1 | [转圈loading] 生成中... 45%
分镜2 | [转圈loading] 排队中...
分镜3 | 未开始

↓ 完成后 ↓

分镜1 | [视频缩略图/首帧] [播放按钮]
分镜2 | [转圈loading] 生成中... 78%
分镜3 | 未开始

点击视频缩略图或播放按钮 → 弹窗播放视频
```

**具体交互：**
1. 选择分镜，点击"生成视频"
2. 立即显示转圈loading UI + 进度百分比
3. 后台轮询任务状态，更新进度
4. 获取到视频链接后，转圈UI替换为视频缩略图（首帧）
5. 点击缩略图或播放按钮 → 弹窗播放视频

**关键点：**
- ✅ 生成中：转圈loading动画
- ✅ 生图完成：显示缩略图，点击放大查看原图
- ✅ 生视频完成：显示视频缩略图（首帧），点击播放
- ✅ 轮询：自动更新UI状态，无需用户手动刷新

**自动轮询策略：**
- 生成中的任务：每5秒轮询一次
- 排队中的任务：每10秒轮询一次
- 已完成/失败：停止轮询
- 用户可以手动点击"刷新"按钮

**手动查看任务：**
- 任务列表页面：显示所有历史任务
- 筛选：全部 / 进行中 / 已完成 / 失败
- 点击任务查看详情和结果

### 4.5 批量操作

**功能：**
1. 批量编辑提示词
   - 选中多个分镜
   - 统一添加前缀/后缀
   - 统一修改某个参数

2. 批量重新生成
   - 选中已生成的分镜
   - 重新生成（覆盖或保留历史版本）

---

## 5. 工作流程示例

### 5.1 完整工作流（分步骤）

```
步骤1：上传和解析
1. 用户上传docx分镜表格
   ↓
2. 后台解析表格结构
   ↓
3. 创建StoryboardSegment记录（25个分镜）
   ↓
4. 显示分镜列表

步骤2：资产提取和提示词生成
5. 用户点击"提取资产"
   ↓
6. LLM分析所有分镜的"镜头内容"
   ↓
7. 提取并创建资产记录：
   - 角色列表（林野、陈默、星禾等）
   - 场景列表（星核主控室、意识对接舱等）
   - 道具列表（照片、数据终端、全息屏幕等）
   - 服装列表（银色维护服等）
   ↓
8. 为每个资产生成图片提示词
   ↓
9. 显示资产管理面板

步骤3：资产准备
10. 用户查看角色列表，发现3个角色未生成人设图
    ↓
11. 用户可以选择：
    - 为角色生成人设图（调用火山方舟API）
    - 从资产库选择已有角色（复用）
    ↓
12. 生成人设图：
    - 查看LLM生成的提示词
    - 编辑提示词（可选）
    - 生成4张候选图
    - 选择满意的一张
    ↓
13. 同样处理场景图、道具图（可选）
    ↓
14. 所有必需资产准备完成 ✓

步骤4：视频提示词生成
15. 用户点击"生成视频提示词"
    ↓
16. LLM为每个分镜生成视频提示词：
    - 基于分镜的"镜头内容"
    - 引用已生成的资产图
    - 结合摄像机参数
    ↓
17. 用户可以查看和编辑视频提示词

步骤5：选择分镜生成视频
18. 用户勾选要生成的分镜（如1-10镜）
    ↓
19. 系统检查：
    - 所有角色都有人设图 ✓
    - 视频提示词已生成 ✓
    - API配置正常 ✓
    ↓
20. 点击"生成选中的分镜"
    ↓
21. 显示生成进度（3/10）
    ↓
22. 生成完成，显示预览
    ↓
23. 不满意可以重新生成，满意则继续生成剩余分镜
```

### 5.2 资产复用场景

```
场景：用户有多个项目，角色"林野"在多个项目中出现

项目A（首次）：
1. 上传脚本，提取到角色"林野"
2. 生成人设图，选择满意的一张
3. 保存到资产库

项目B（复用）：
1. 上传新脚本，也有"林野"角色
2. 系统提示：检测到资产库中有同名角色"林野"
3. 用户选择：
   - 使用资产库中的"林野"（复用人设图）✓
   - 创建新的"林野"（重新生成人设图）
4. 用户选择复用，直接应用已有人设图
5. 跳过步骤3，直接进入步骤4生成视频提示词
```

### 5.3 LLM优化分镜场景（可选，下一步）

```
场景：用户想要统一风格或优化分镜

1. 上传分镜表格，完成基础解析
   ↓
2. 用户点击"LLM优化分镜"
   ↓
3. 选择风格：
   - 写实风格
   - 动漫风格
   - 科幻风格
   - 奇幻风格
   ↓
4. LLM分析所有分镜，生成优化建议：
   - 调整描述以符合风格
   - 优化镜头衔接
   - 建议增删分镜
   ↓
5. 显示优化前后对比
   ↓
6. 用户确认应用优化
   ↓
7. 更新分镜表格
   ↓
8. 继续步骤2：提取资产
```

---

## 6. 技术实现建议

### 6.1 数据库模型调整

**保留现有模型：**
- `Project`: 剧本项目
- `Script`: 脚本文档（一个项目多个脚本）
- `StoryboardSegment`: 分镜片段

**新增模型：**

```python
# 角色模型
class Character(Base):
    id: int
    script_id: int  # 关联脚本
    name: str  # 角色名称
    appearance_description: str  # 外观描述
    reference_prompt: str  # LLM生成的人设图提示词
    candidate_images_json: JSON  # 4张候选图URL
    selected_image_path: str  # 选中的人设图
    user_asset_id: int  # 关联到资产库（可选）
    first_appearance_segment: int  # 首次出场分镜号
    total_appearances: int  # 总出场次数

# 场景模型
class Scene(Base):
    id: int
    script_id: int
    name: str  # 场景名称
    scene_type: str  # 室内/室外
    description: str
    image_prompt: str  # LLM生成的场景图提示词
    reference_image_path: str  # 场景参考图
    user_asset_id: int  # 关联到资产库（可选）

# 道具模型
class Item(Base):
    id: int
    script_id: int
    name: str
    description: str
    image_prompt: str
    reference_image_path: str
    user_asset_id: int

# 服装模型
class Costume(Base):
    id: int
    character_id: int  # 关联角色
    name: str  # 服装名称（银色维护服）
    description: str
    image_prompt: str
    reference_image_path: str

# 分镜资产关联（记录每个分镜使用了哪些资产）
class SegmentAsset(Base):
    id: int
    segment_id: int  # 关联分镜
    asset_type: Enum  # character/scene/item/costume
    asset_id: int  # 资产ID
    override_description: str  # 覆盖描述（可选）
```

**修改StoryboardSegment模型：**
```python
# 添加字段
video_prompt: str  # LLM生成的视频提示词
video_prompt_edited: str  # 用户编辑后的提示词
generation_status: Enum  # pending/queued/generating/completed/failed
generation_task_id: str  # 火山方舟任务ID
generation_progress: int  # 生成进度 0-100
video_path: str  # 生成的视频路径
video_thumbnail_path: str  # 视频缩略图
generation_error: str  # 失败原因
created_at: datetime
updated_at: datetime
```

**修改Character模型：**
```python
# 添加字段
generation_status: Enum  # pending/generating/completed/failed
generation_task_ids: JSON  # 4张候选图的任务ID（如果有）
generation_progress: int  # 生成进度
candidate_images_json: JSON  # 4张候选图URL和缩略图
selected_image_path: str  # 选中的人设图
selected_image_thumbnail: str  # 选中图的缩略图
generation_error: str  # 失败原因
```

**新增GenerationTask模型（统一任务管理）：**
```python
class GenerationTask(Base):
    id: int
    task_type: Enum  # character_image/scene_image/item_image/video
    target_id: int  # 关联的资产或分镜ID
    external_task_id: str  # 火山方舟返回的任务ID
    status: Enum  # queued/generating/completed/failed
    progress: int  # 0-100
    result_url: str  # 生成结果URL
    thumbnail_url: str  # 缩略图URL
    error_message: str
    started_at: datetime
    completed_at: datetime
    created_at: datetime
    updated_at: datetime
```

### 6.2 API端点规划

**解析相关：**
- `POST /projects/{id}/scripts/upload` - 上传脚本，触发解析
- `GET /scripts/{id}/parsing-progress` - 获取解析进度
- `GET /scripts/{id}/parsing-result` - 获取解析结果（分镜+资产）

**资产管理：**
- `GET /scripts/{id}/characters` - 获取角色列表（支持筛选）
- `POST /characters/{id}/generate-images` - 生成角色人设图（4张候选）
- `POST /characters/{id}/select-image` - 选择人设图
- `PUT /characters/{id}/prompt` - 编辑角色提示词
- `GET /scripts/{id}/scenes` - 获取场景列表
- `GET /scripts/{id}/items` - 获取道具列表

**提示词管理：**
- `GET /storyboards/{id}/prompt` - 获取分镜视频提示词
- `PUT /storyboards/{id}/prompt` - 编辑分镜视频提示词
- `POST /storyboards/batch-edit-prompt` - 批量编辑提示词

**生成管理：**
- `POST /scripts/{id}/generate-videos` - 生成选中的分镜视频
  - 请求体：`{"segment_ids": [1, 2, 3]}`
  - 返回：任务ID列表
- `GET /generation/tasks/{task_id}` - 查询单个任务进度
  - 返回：状态、进度、结果URL
- `GET /generation/tasks/batch` - 批量查询任务进度
  - 请求体：`{"task_ids": ["task1", "task2"]}`
- `POST /generation/{task_id}/cancel` - 取消生成
- `GET /scripts/{id}/generation-status` - 获取脚本所有分镜的生成状态

**任务管理：**
- `GET /generation/tasks` - 获取用户所有任务列表（支持筛选）
- `GET /generation/tasks/active` - 获取进行中的任务
- `POST /generation/tasks/poll` - 轮询更新任务状态（后台定时任务）

**资产库：**
- `GET /user-assets` - 获取用户资产库（支持类型筛选）
- `POST /characters/{id}/save-to-library` - 保存角色到资产库
- `POST /characters/{id}/load-from-library` - 从资产库加载角色

### 6.3 LLM集成

**Prompt模板：**

```python
# 资产提取Prompt
ASSET_EXTRACTION_PROMPT = """
分析以下分镜内容，提取角色、场景、道具信息，并生成英文提示词。

分镜内容：{segment_content}

请以JSON格式输出：
{{
  "scene": {{"name": "场景名", "type": "室内/室外", "description": "描述", "image_prompt": "英文提示词"}},
  "characters": [{{"name": "角色名", "appearance": "外观", "action": "动作", "reference_prompt": "英文提示词"}}],
  "items": [{{"name": "道具名", "description": "描述", "image_prompt": "英文提示词"}}],
  "video_prompt": "完整的视频生成英文提示词"
}}
"""

# 视频提示词生成Prompt
VIDEO_PROMPT_GENERATION = """
基于以下信息生成视频提示词：

景别：{shot_type}
镜头内容：{content}
台词：{dialogue}
摄像机运动：{camera_movement}
转场方式：{transition}

生成一个完整的英文视频提示词，包含场景、角色、动作、镜头信息。
"""
```

### 6.4 前端组件规划

**新增/修改组件：**
- `ScriptListView` - 脚本列表页（已有）
- `StoryboardView` - 分镜管理页（修改）
  - `CharacterPanel` - 角色管理面板（新增）
    - `CharacterCard` - 角色卡片，显示生成状态和缩略图
    - `ImageGenerationModal` - 图片生成弹窗，显示4张候选图
    - `ImageViewerModal` - 原图查看弹窗
  - `ScenePanel` - 场景管理面板（新增）
  - `ItemPanel` - 道具管理面板（新增）
  - `StoryboardTable` - 分镜列表表格（修改，添加多选和状态显示）
  - `PromptEditor` - 提示词编辑器（新增）
  - `GenerationProgressModal` - 生成进度弹窗（新增）
    - 显示实时进度条
    - 显示每个分镜的状态
    - 支持暂停/取消/后台运行
- `TaskListView` - 任务列表页（新增）
  - 显示所有历史任务
  - 筛选和查看任务详情
- `AssetLibraryModal` - 资产库弹窗（新增）

**前端轮询逻辑：**
```javascript
// 自动轮询生成任务
const pollGenerationTasks = async (taskIds) => {
  const interval = setInterval(async () => {
    const response = await fetch('/generation/tasks/batch', {
      method: 'POST',
      body: JSON.stringify({ task_ids: taskIds })
    });
    const tasks = await response.json();
    
    // 更新UI状态
    tasks.forEach(task => {
      if (task.status === 'completed') {
        // 生成完成：显示缩略图
        updateUIWithThumbnail(task.target_id, task.thumbnail_url, task.result_url);
      } else if (task.status === 'generating') {
        // 生成中：显示转圈loading + 进度
        updateUIWithProgress(task.target_id, task.progress);
      } else if (task.status === 'failed') {
        // 失败：显示错误
        updateUIWithError(task.target_id, task.error_message);
      }
    });
    
    // 检查是否所有任务完成
    const allCompleted = tasks.every(t => 
      t.status === 'completed' || t.status === 'failed'
    );
    
    if (allCompleted) {
      clearInterval(interval);
      showCompletionNotification();
    }
  }, 5000); // 每5秒轮询一次
  
  return interval;
};

// 生图UI渲染
const renderImageGeneration = (character) => {
  return (
    <div className="character-images">
      {[0, 1, 2, 3].map(index => {
        const image = character.candidate_images[index];
        
        if (!image || image.status === 'generating') {
          // 生成中：显示转圈loading
          return (
            <div key={index} className="image-slot">
              <LoadingSpinner />
              <span>生成中...</span>
            </div>
          );
        } else if (image.status === 'completed') {
          // 完成：显示缩略图
          return (
            <div key={index} className="image-slot" 
                 onClick={() => viewOriginalImage(image.url)}>
              <img src={image.thumbnail_url} alt={`候选图${index + 1}`} />
            </div>
          );
        }
      })}
    </div>
  );
};

// 生视频UI渲染
const renderVideoGeneration = (segment) => {
  if (segment.generation_status === 'generating') {
    // 生成中：转圈loading + 进度
    return (
      <div className="video-generating">
        <LoadingSpinner />
        <span>生成中... {segment.generation_progress}%</span>
        <ProgressBar value={segment.generation_progress} />
      </div>
    );
  } else if (segment.generation_status === 'completed') {
    // 完成：显示视频缩略图
    return (
      <div className="video-completed" onClick={() => playVideo(segment.video_path)}>
        <img src={segment.video_thumbnail_path} alt="视频缩略图" />
        <PlayButton />
      </div>
    );
  } else if (segment.generation_status === 'failed') {
    // 失败：显示错误和重试按钮
    return (
      <div className="video-failed">
        <span>❌ 生成失败: {segment.generation_error}</span>
        <button onClick={() => retryGeneration(segment.id)}>重试</button>
      </div>
    );
  } else {
    // 未开始
    return <span>未开始</span>;
  }
};

// 查看原图弹窗
const viewOriginalImage = (imageUrl) => {
  showModal({
    content: <img src={imageUrl} style={{maxWidth: '100%'}} />,
    footer: <button onClick={() => selectImage(imageUrl)}>选择此图</button>
  });
};

// 播放视频弹窗
const playVideo = (videoUrl) => {
  showModal({
    content: <video src={videoUrl} controls autoplay style={{maxWidth: '100%'}} />,
    size: 'large'
  });
};
```

---

## 7. 实施优先级

### P0（核心功能，必须实现）
1. ✅ Script模型和多脚本支持（已完成）
2. ✅ Character模型（已完成）
3. **步骤1：解析docx分镜表格**
4. **步骤2：LLM提取资产和生成资产图提示词**
5. **步骤3：角色管理 - 显示全部角色、筛选、生成人设图**
6. **步骤3：资产库复用 - 选择已有资产**
7. **步骤4：LLM生成视频提示词（基于已有资产）**
8. **步骤5：分镜选择 - 多选分镜、生成选中的分镜**
9. **任务进度管理 - 轮询查询、状态显示、缩略图预览**

### P1（重要功能，尽快实现）
1. 场景和道具管理（步骤3扩展）
2. 提示词编辑器（查看和编辑LLM生成的提示词）
3. 生成前检查（检查资产完整性）
4. 服装管理
5. 任务列表页面（查看所有历史任务）
6. 原图/原视频查看弹窗
7. 失败重试机制

### P2（增强功能，逐步实现）
1. **LLM优化分镜（风格选择、镜头优化）**
2. 提示词模板和批量编辑
3. 资产引用语法（@角色 #场景 $道具）
4. 一致性检查
5. 批量操作（批量生成、批量编辑）

### P3（高级功能，长期规划）
1. 版本管理（保留生成历史）
2. 智能推荐（根据场景推荐镜头）
3. 协作功能
4. 统计分析
5. 高级导出功能

---

## 8. 批注区

**请在下方或相应章节添加您的想法、需求和优先级调整：**

### 关于分镜表格解析：


### 关于LLM提示词生成：


### 关于资产管理：


### 关于分镜选择和生成：


### 其他想法：


---

## 附录：关键差异说明

### 原方案 vs 修正方案

| 方面 | 原方案（错误） | 修正方案（正确） |
|------|---------------|-----------------|
| **输入** | 剧本文本 | 已结构化的分镜表格 |
| **LLM作用** | 将剧本转换为分镜 | 从分镜提取资产并生成提示词 |
| **解析目标** | 创建分镜 | 提取角色/场景/道具，生成提示词 |
| **提示词用途** | 未明确 | 分两层：资产图提示词 + 视频提示词 |
| **工作流** | 剧本→分镜→生成 | 分镜表格→资产提取→提示词→生成 |

### 核心理解

1. **docx已包含完整分镜表格**，不需要LLM创建分镜
2. **解析是分步骤的**：
   - 步骤1：解析表格结构
   - 步骤2：LLM提取资产并生成资产图提示词
   - 步骤3：用户生成资产图或选择复用
   - 步骤4：LLM生成视频提示词（基于已有资产）
   - 步骤5：用户选择分镜生成视频
3. **LLM的两个作用**：
   - 作用1：理解"镜头内容"，提取资产，生成资产图提示词
   - 作用2：基于已有资产，生成视频提示词
4. **两层提示词**：资产图提示词（人设图/场景图）+ 视频提示词
5. **资产管理是核心**：角色、场景、道具需要独立管理和复用
6. **选择性生成**：用户可以只生成部分分镜，不是全部生成
7. **LLM可以优化分镜**（可选，P2优先级）：
   - 用户可以选择让LLM综合优化分镜
   - 根据风格选择调整优化方向
   - 优化镜头衔接、叙事节奏等

# API 端点修复总结

## 问题描述
前端调用的 API 端点路径与后端实际端点不匹配，导致资产提取功能无法正常工作。

## 修复的端点

### 1. 脚本上传
- **旧路径**: `/projects/{project_id}/upload-docx`
- **新路径**: `/scripts/projects/{project_id}/upload`
- **返回**: 包含 `id` 字段的 Script 对象

### 2. 解析进度查询
- **旧路径**: `/projects/{project_id}/parsing-progress`
- **新路径**: `/scripts/{script_id}/parsing-progress`
- **说明**: 现在使用 script_id 而不是 project_id

### 3. 脚本列表
- **路径**: `/scripts/projects/{project_id}/list`
- **说明**: 获取项目下的所有脚本

### 4. 资产提取
- **旧路径**: `/scripts/{script_id}/extract-assets`
- **新路径**: `/asset-management/scripts/{script_id}/extract-assets`
- **方法**: POST

### 5. 资产列表查询
- **角色**: `/characters/scripts/{script_id}/list`
- **场景**: `/asset-management/scripts/{script_id}/scenes`
- **道具**: `/asset-management/scripts/{script_id}/items`
- **服装**: `/asset-management/scripts/{script_id}/costumes`

### 6. 生成提示词
- **路径**: `/asset-management/generate-prompt`
- **方法**: POST
- **请求体**:
  ```json
  {
    "asset_type": "character|scene|item|costume",
    "asset_name": "资产名称",
    "asset_description": "资产描述",
    "additional_context": "额外上下文（可选）"
  }
  ```

### 7. 角色生成图像
- **路径**: `/characters/{character_id}/generate-images`
- **方法**: POST
- **说明**: 为角色生成4张候选人设图

### 8. 其他资产生成图像
- **路径**: `/generation-tasks`
- **方法**: POST
- **请求体**:
  ```json
  {
    "task_type": "scene_image|item_image|costume_image",
    "target_id": 123,
    "prompt": "生成提示词"
  }
  ```

## 前端修改

### 1. 添加调试日志
在关键函数中添加了 `console.log` 和 `console.error`，方便调试：
- `loadScript()` - 加载脚本列表
- `handleExtractAssets()` - 提取资产
- `loadAssets()` - 加载资产列表
- `handleGeneratePrompt()` - 生成提示词
- `handleGenerateImage()` - 生成图像

### 2. 修正上传流程
- 上传后从响应中获取 `script_id`
- 使用 `script_id` 轮询解析进度
- 将 `script_id` 保存到状态中供后续使用

### 3. 修正资产管理流程
- 角色使用专门的 `/characters` 端点
- 其他资产使用 `/asset-management` 端点
- 生成提示词统一使用 `/asset-management/generate-prompt`

## 测试步骤

1. **上传脚本**
   - 点击"上传Word文档"
   - 选择 docx 文件
   - 观察控制台输出 `Script uploaded, scriptId: X`
   - 等待解析完成

2. **提取资产**
   - 点击"提取资产"按钮
   - 点击"开始提取"
   - 观察控制台输出 `Extracting assets for scriptId: X`
   - 等待提取完成

3. **查看资产**
   - 点击"角色"/"场景"/"道具"/"服装"按钮
   - 观察控制台输出 `Loading assets from: /api/v1/...`
   - 查看资产列表

4. **生成提示词**
   - 在资产列表中点击"生成提示词"
   - 观察控制台输出 `Generating prompt for asset: {...}`
   - 等待提示词生成完成

5. **生成图像**
   - 在资产列表中点击"生成图像"
   - 观察控制台输出 `Generating image for asset: {...}`
   - 等待图像生成完成

## 注意事项

1. 所有 API 调用都需要认证 token
2. 解析进度轮询使用 script_id 而不是 project_id
3. 角色生成图像使用专门的端点，返回4张候选图
4. 其他资产生成图像使用通用的生成任务系统
5. 前端控制台会输出详细的调试信息，便于排查问题

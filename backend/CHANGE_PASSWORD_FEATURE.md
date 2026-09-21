# 修改密码功能文档

## 功能说明

在个人中心添加了修改密码的功能，支持两种方式：

### 方式1：使用旧密码修改
适用于用户记得旧密码的情况。

### 方式2：使用邮箱验证码修改
适用于以下场景：
- 用户忘记了旧密码
- 用户首次设置密码（如果注册时没有设置密码）

## API端点

### POST /user/change-password

修改当前用户的密码。

**请求头：**
```
Authorization: Bearer <access_token>
```

**请求体：**

#### 方式1：使用旧密码
```json
{
  "old_password": "旧密码",
  "new_password": "新密码"
}
```

#### 方式2：使用邮箱验证码
```json
{
  "verification_code": "123456",
  "new_password": "新密码"
}
```

**字段说明：**
- `old_password` (可选): 旧密码，如果提供则使用旧密码验证
- `new_password` (必填): 新密码，长度6-50个字符
- `verification_code` (可选): 邮箱验证码，如果不提供旧密码则必须提供验证码

**响应：**

成功 (200):
```json
{
  "message": "密码修改成功"
}
```

失败 (400):
```json
{
  "detail": "旧密码错误"
}
```
或
```json
{
  "detail": "验证码无效或已过期"
}
```
或
```json
{
  "detail": "请提供旧密码或邮箱验证码"
}
```

## 使用流程

### 场景1：用户记得旧密码

1. 用户在个人中心点击"修改密码"
2. 输入旧密码和新密码
3. 提交请求
4. 系统验证旧密码是否正确
5. 更新密码

### 场景2：用户忘记密码或首次设置密码

1. 用户在个人中心点击"修改密码"
2. 点击"忘记密码？使用邮箱验证"
3. 调用 `POST /auth/send-code` 发送验证码到用户邮箱
4. 输入验证码和新密码
5. 提交请求
6. 系统验证验证码是否正确
7. 更新密码

## 前端实现示例

```javascript
// 方式1：使用旧密码
async function changePasswordWithOld(oldPassword, newPassword) {
  const response = await fetch('/user/change-password', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      old_password: oldPassword,
      new_password: newPassword
    })
  });
  
  if (response.ok) {
    alert('密码修改成功');
  } else {
    const error = await response.json();
    alert(error.detail);
  }
}

// 方式2：使用验证码
async function changePasswordWithCode(verificationCode, newPassword) {
  const response = await fetch('/user/change-password', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      verification_code: verificationCode,
      new_password: newPassword
    })
  });
  
  if (response.ok) {
    alert('密码修改成功');
  } else {
    const error = await response.json();
    alert(error.detail);
  }
}

// 发送验证码
async function sendVerificationCode(email) {
  const response = await fetch('/auth/send-code', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ email })
  });
  
  if (response.ok) {
    alert('验证码已发送到您的邮箱');
  }
}
```

## 安全性

1. **密码长度限制**：新密码必须在6-50个字符之间
2. **验证码过期**：邮箱验证码有效期为10分钟（600秒）
3. **旧密码验证**：使用bcrypt进行密码哈希验证
4. **需要登录**：必须提供有效的JWT token才能修改密码

## 数据库变更

无需数据库迁移，使用现有的 `users.password_hash` 字段。

## 代码变更

### 新增文件
无

### 修改文件
1. `/root/seedance-studio/backend/app/schemas/user.py`
   - 添加 `ChangePasswordRequest` schema

2. `/root/seedance-studio/backend/app/api/v1/endpoints/user.py`
   - 添加 `POST /change-password` 端点
   - 导入必要的依赖（security, email_service等）

3. `/root/seedance-studio/backend/app/repositories/user_repository.py`
   - 添加 `update_password()` 方法

## 测试

### 手动测试步骤

1. **测试使用旧密码修改**
```bash
# 先登录获取token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "oldpass123"}'

# 使用旧密码修改
curl -X POST http://localhost:8000/user/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"old_password": "oldpass123", "new_password": "newpass123"}'
```

2. **测试使用验证码修改**
```bash
# 发送验证码
curl -X POST http://localhost:8000/auth/send-code \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# 使用验证码修改密码
curl -X POST http://localhost:8000/user/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"verification_code": "123456", "new_password": "newpass123"}'
```

3. **测试错误情况**
```bash
# 旧密码错误
curl -X POST http://localhost:8000/user/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"old_password": "wrongpass", "new_password": "newpass123"}'

# 验证码错误
curl -X POST http://localhost:8000/user/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"verification_code": "000000", "new_password": "newpass123"}'

# 既不提供旧密码也不提供验证码
curl -X POST http://localhost:8000/user/change-password \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"new_password": "newpass123"}'
```

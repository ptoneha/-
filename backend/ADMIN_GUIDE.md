# 管理系统使用指南

## 📖 目录
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [API接口文档](#api接口文档)
- [权限说明](#权限说明)
- [常见问题](#常见问题)

---

## 系统架构

### 功能模块

```
管理系统
├── 认证模块 (/admin/auth)
│   ├── 登录/登出
│   ├── 密码管理
│   └── Token验证
│
├── 文档管理 (/admin/docs)
│   ├── 文档列表/详情
│   ├── 文档编辑/删除
│   └── 批量操作
│
├── 分片管理 (/admin/chunks)
│   ├── 分片列表/详情
│   ├── 分片审核
│   ├── 质量评分
│   └── 批量操作
│
├── 题库管理 (/admin/questions)
│   ├── 题目列表/详情
│   ├── 题目编辑/删除
│   └── 批量操作
│
├── 用户管理 (/admin/users)
│   ├── 用户CRUD
│   └── 角色权限管理
│
├── 审计日志 (/admin/audit)
│   ├── 操作日志查询
│   ├── 用户活动追踪
│   └── 统计分析
│
└── 统计分析 (/admin/stats)
    ├── 系统概览
    ├── 内容分布
    ├── 质量报告
    └── 使用统计
```

---

## 快速开始

### 1. 安装依赖

```bash
cd chaoX/backend
pip install -r requirements.txt
```

### 2. 初始化数据库

启动应用时会自动初始化管理系统数据库：

```bash
uvicorn app:app --reload --port 8787
```

### 3. 默认管理员账号

- **用户名**: `admin`
- **密码**: `admin123`
- **角色**: `superadmin`

⚠️ **首次登录后请立即修改密码！**

### 4. 登录获取Token

```bash
curl -X POST http://localhost:8787/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

响应：
```json
{
  "ok": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "user_id": 1,
    "username": "admin",
    "role": "superadmin"
  }
}
```

### 5. 使用Token访问API

在后续请求中，在Header中携带Token：

```bash
curl -X GET http://localhost:8787/admin/stats/dashboard \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## API接口文档

### 认证相关 (/admin/auth)

#### POST /admin/auth/login
登录获取Token

**请求体：**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**响应：**
```json
{
  "ok": true,
  "access_token": "token_string",
  "token_type": "bearer",
  "user": {...}
}
```

#### GET /admin/auth/me
获取当前用户信息（需要Token）

#### POST /admin/auth/change-password
修改密码

**请求体：**
```json
{
  "old_password": "old_pass",
  "new_password": "new_pass"
}
```

---

### 文档管理 (/admin/docs)

#### GET /admin/docs
获取文档列表

**查询参数：**
- `source`: 来源过滤 (kb/qb)
- `search`: 搜索关键词
- `limit`: 每页数量 (默认20)
- `offset`: 偏移量 (默认0)

#### GET /admin/docs/{doc_id}
获取文档详情

#### PUT /admin/docs/{doc_id}
更新文档

**请求体：**
```json
{
  "title": "新标题",
  "chapter": 1,
  "section_number": 2,
  "is_published": true
}
```

#### DELETE /admin/docs/{doc_id}
删除文档

**查询参数：**
- `hard_delete`: 是否硬删除 (默认false)

#### POST /admin/docs/batch-delete
批量删除文档

**请求体：**
```json
{
  "doc_ids": [1, 2, 3],
  "hard_delete": false
}
```

---

### 分片管理 (/admin/chunks)

#### GET /admin/chunks
获取分片列表

**查询参数：**
- `doc_id`: 文档ID
- `kind`: 类型过滤 (definition/theorem/formula/example)
- `search`: 搜索关键词
- `verified_only`: 仅显示已审核
- `limit`: 每页数量
- `offset`: 偏移量

#### PUT /admin/chunks/{chunk_id}
更新分片

**请求体：**
```json
{
  "content_md": "新内容",
  "kind": "theorem",
  "is_verified": true,
  "quality_score": 85
}
```

#### POST /admin/chunks/batch-verify
批量审核分片

**请求体：**
```json
{
  "chunk_ids": [1, 2, 3],
  "verified": true
}
```

---

### 题库管理 (/admin/questions)

#### GET /admin/questions
获取题目列表

#### PUT /admin/questions/{qid}
更新题目

#### DELETE /admin/questions/{qid}
删除题目

---

### 用户管理 (/admin/users)

#### GET /admin/users
获取用户列表（需要admin权限）

#### POST /admin/users
创建新用户（需要superadmin权限）

**请求体：**
```json
{
  "username": "newuser",
  "password": "password123",
  "full_name": "新用户",
  "email": "user@example.com",
  "role": "editor"
}
```

#### PUT /admin/users/{user_id}
更新用户信息

#### DELETE /admin/users/{user_id}
删除用户（需要superadmin权限）

---

### 统计分析 (/admin/stats)

#### GET /admin/stats/dashboard
获取仪表板数据

**响应：**
```json
{
  "ok": true,
  "system_stats": {
    "total_docs": 100,
    "total_chunks": 500,
    "total_questions": 200
  },
  "recent_uploads": [...],
  "top_searches": [...],
  "storage_usage": {...},
  "upload_trend": [...]
}
```

#### GET /admin/stats/content-distribution
获取内容分布统计

#### GET /admin/stats/quality-report
获取质量报告

#### GET /admin/stats/usage?days=30
获取使用统计

---

### 审计日志 (/admin/audit)

#### GET /admin/audit/logs
获取审计日志列表

**查询参数：**
- `user_id`: 用户ID
- `action`: 操作类型
- `resource_type`: 资源类型
- `limit`: 每页数量
- `offset`: 偏移量

#### GET /admin/audit/activity/{user_id}?days=7
获取用户活动统计

#### GET /admin/audit/action-stats?days=30
获取操作统计

---

## 权限说明

### 角色层级

1. **superadmin** (超级管理员)
   - 最高权限
   - 可以创建/删除用户
   - 可以执行所有操作

2. **admin** (管理员)
   - 可以管理内容
   - 可以查看审计日志
   - 不能管理其他管理员

3. **editor** (编辑)
   - 可以编辑内容
   - 可以审核分片
   - 不能删除用户

4. **viewer** (查看者)
   - 只读权限
   - 可以查看统计数据
   - 不能修改任何内容

### 权限检查

每个API端点都有权限要求，示例：

```python
@router.get("/docs")
async def list_docs(current_user: dict = Depends(require_editor)):
    # 需要 editor 或更高权限
    pass

@router.post("/users")
async def create_user(current_user: dict = Depends(require_superadmin)):
    # 需要 superadmin 权限
    pass
```

---

## 常见问题

### Q: 忘记管理员密码怎么办？

A: 可以直接在数据库中重置：

```sql
-- 重置为 admin123
UPDATE public.admin_user 
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lE7X9fKJ5jO6'
WHERE username = 'admin';
```

### Q: JWT Token过期时间是多久？

A: 默认24小时。可以在 `utils/jwt_handler.py` 中修改 `ACCESS_TOKEN_EXPIRE_MINUTES`。

### Q: 如何修改JWT密钥？

A: 设置环境变量：

```bash
export JWT_SECRET_KEY="your-super-secret-key-here"
```

或在 `.env` 文件中：

```
JWT_SECRET_KEY=your-super-secret-key-here
```

### Q: 软删除和硬删除的区别？

A: 
- **软删除**：设置 `deleted_at` 字段，数据仍在数据库中，可以恢复
- **硬删除**：从数据库中物理删除，无法恢复

### Q: 如何查看完整的API文档？

A: 启动服务后访问：
- Swagger UI: http://localhost:8787/docs
- ReDoc: http://localhost:8787/redoc

---

## 安全建议

1. ✅ 生产环境必须修改 JWT_SECRET_KEY
2. ✅ 修改默认管理员密码
3. ✅ 定期检查审计日志
4. ✅ 使用HTTPS传输
5. ✅ 限制管理后台访问IP
6. ✅ 定期备份数据库

---

## 技术支持

如有问题，请查看：
- 应用日志
- 审计日志
- PostgreSQL日志

或联系系统管理员。


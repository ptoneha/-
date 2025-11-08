# ⚡ 快速开始指南

5分钟快速启动 ChaoX 知识库管理系统！

---

## 🎯 Step 1: 环境准备

### 方式A: Docker（推荐）

```bash
# 确认Docker已安装
docker --version
docker-compose --version
```

### 方式B: 本地开发

```bash
# Python 3.11+
python --version

# PostgreSQL 15+
psql --version
```

---

## 🚀 Step 2: 启动服务

### 方式A: 使用Docker

```bash
# 进入项目目录
cd chaoX

# 启动所有服务（PostgreSQL + Backend）
docker-compose up -d

# 查看日志
docker-compose logs -f backend
```

**等待数据库初始化完成（约10-15秒）**

### 方式B: 本地开发

```bash
# 1. 启动PostgreSQL
docker-compose up -d pg

# 2. 安装Python依赖
cd backend
pip install -r requirements.txt

# 3. 初始化管理系统（可选）
python init_admin.py

# 4. 启动后端
uvicorn app:app --reload --port 8787
```

---

## ✅ Step 3: 验证服务

打开浏览器访问：

- **API文档**: http://localhost:8787/docs
- **健康检查**: http://localhost:8787/health
- **管理系统健康**: http://localhost:8787/admin/health

看到 `{"ok": true}` 说明服务正常！

---

## 🔐 Step 4: 登录管理后台

### 使用curl测试

```bash
curl -X POST http://localhost:8787/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

**成功响应：**
```json
{
  "ok": true,
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": {
    "user_id": 1,
    "username": "admin",
    "role": "superadmin"
  }
}
```

### 使用Postman或其他工具

1. 打开 http://localhost:8787/docs
2. 点击 `/admin/auth/login` 接口
3. 点击 "Try it out"
4. 输入用户名密码
5. 点击 "Execute"
6. 复制返回的 `access_token`

---

## 🎮 Step 5: 尝试API

### 5.1 查看仪表板数据

```bash
# 替换 YOUR_TOKEN 为上一步获得的token
curl -X GET http://localhost:8787/admin/stats/dashboard \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5.2 获取文档列表

```bash
curl -X GET http://localhost:8787/admin/docs \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5.3 上传一个测试文档（用户端API）

```bash
curl -X POST http://localhost:8787/ingest \
  -F "file=@your_document.docx" \
  -F "chapter=1" \
  -F "section_number=1"
```

### 5.4 搜索知识库（用户端API）

```bash
curl -X GET "http://localhost:8787/search?q=极限&limit=5"
```

---

## 📱 Step 6: 启动前端（可选）

```bash
cd chaoX/frontend

# 安装依赖
npm install

# 开发模式
npm run dev

# 或构建生产版本
npm run build
npx serve -s dist -l 5173
```

访问: http://localhost:5173

---

## 🔧 常用操作

### 修改管理员密码

```bash
curl -X POST http://localhost:8787/admin/auth/change-password \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "admin123",
    "new_password": "new_secure_password"
  }'
```

### 创建新用户（需要superadmin权限）

```bash
curl -X POST http://localhost:8787/admin/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "editor1",
    "password": "password123",
    "full_name": "编辑一号",
    "email": "editor1@example.com",
    "role": "editor"
  }'
```

### 查看审计日志

```bash
curl -X GET http://localhost:8787/admin/audit/logs \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📚 完整功能探索

### 在API文档中测试

1. 访问 http://localhost:8787/docs
2. 点击右上角 "Authorize" 按钮
3. 输入: `Bearer YOUR_TOKEN`（注意Bearer后有空格）
4. 点击 "Authorize"
5. 现在可以直接在文档中测试所有API！

### 查看所有可用API

- **认证**: `/admin/auth/*`
- **文档管理**: `/admin/docs/*`
- **分片管理**: `/admin/chunks/*`
- **题库管理**: `/admin/questions/*`
- **用户管理**: `/admin/users/*`
- **统计分析**: `/admin/stats/*`
- **审计日志**: `/admin/audit/*`

---

## 🎯 核心功能演示

### 完整工作流程示例

```bash
# 1. 登录
TOKEN=$(curl -s -X POST http://localhost:8787/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# 2. 上传文档（用户端API，无需token）
curl -X POST http://localhost:8787/ingest \
  -F "file=@test.docx" \
  -F "chapter=1" \
  -F "section_number=1"

# 3. 查看文档列表
curl -X GET http://localhost:8787/admin/docs \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.data[] | {doc_id, title, chunk_count}'

# 4. 查看分片列表
curl -X GET "http://localhost:8787/admin/chunks?limit=5" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.data[] | {chunk_id, kind, h2}'

# 5. 审核分片
curl -X POST http://localhost:8787/admin/chunks/batch-verify \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chunk_ids":[1,2,3],"verified":true}'

# 6. 查看统计数据
curl -X GET http://localhost:8787/admin/stats/dashboard \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.system_stats'

# 7. 查看操作日志
curl -X GET http://localhost:8787/admin/audit/logs \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.data[] | {action, resource_type, created_at}'
```

---

## 🐛 遇到问题？

### 问题1: 无法连接数据库

```bash
# 检查PostgreSQL是否运行
docker-compose ps

# 重启服务
docker-compose restart pg
docker-compose restart backend
```

### 问题2: Token无效

- 检查Token是否包含 "Bearer " 前缀
- Token默认24小时过期，需要重新登录

### 问题3: 权限不足

- 检查当前用户角色
- 某些操作需要admin或superadmin权限

### 问题4: 端口被占用

```bash
# 修改端口（docker-compose.yml）
ports:
  - "8788:8787"  # 改为8788
```

---

## 📖 下一步

- 📘 **详细文档**: 阅读 [ADMIN_GUIDE.md](./backend/ADMIN_GUIDE.md)
- 🚀 **部署指南**: 查看 [DEPLOYMENT.md](./backend/DEPLOYMENT.md)  
- 🏗️ **架构设计**: 了解 [ARCHITECTURE.md](./ARCHITECTURE.md)
- 🧪 **API示例**: 参考 [example_requests.http](./backend/example_requests.http)

---

## ✨ 恭喜！

你已经成功启动了 ChaoX 管理系统！

现在你可以：
- ✅ 上传和管理文档
- ✅ 审核和编辑分片
- ✅ 管理题库
- ✅ 创建用户和分配权限
- ✅ 查看统计数据和审计日志

**开始构建你的知识库吧！** 🎉

---

需要帮助？
- 查看文档目录
- 访问API文档: http://localhost:8787/docs
- 检查日志: `docker-compose logs -f backend`


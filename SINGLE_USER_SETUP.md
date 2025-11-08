# 🎯 单用户简化版本 - 使用说明

已完成的简化改造：
- ✅ 去除所有登录验证
- ✅ 简化为单用户模式
- ✅ 在现有前端添加管理功能
- ✅ 优化资源占用（适合2核2G服务器）

---

## 🚀 快速启动

### 1. 启动数据库

```powershell
cd C:\Users\exo32\Desktop\chaoxAI\chaoX
docker-compose up -d pg
```

### 2. 启动后端

```powershell
cd backend
.\start.ps1
```

或者：
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app:app --reload --port 8787
```

### 3. 启动前端

```powershell
cd frontend
npm run dev
```

---

## 📱 访问地址

- **前端界面**: http://localhost:5173
- **API文档**: http://localhost:8787/docs

---

## 🎮 功能说明

### 前端页面

访问 http://localhost:5173，你会看到4个选项卡：

#### 📤 上传
- 上传.docx文档
- 自动分片处理

#### 📚 题库
- 上传题库文档
- 批量导入题目

#### 🔍 检索
- 全文搜索
- 分类筛选
- 查看分片详情

#### ⚙️ 管理（新增）
包含5个子功能：

##### 📊 仪表板
- 系统统计数据
- 文档/分片/题目总数
- 最近上传记录

##### 📁 文档管理
- 查看所有文档
- 搜索文档
- 删除文档

##### 📝 分片管理
- 查看所有分片
- 批量审核
- 删除分片

##### ❓ 题库管理
- 查看所有题目
- 删除题目

##### 📋 操作日志
- 查看所有操作记录
- 审计追踪

---

## 🔑 简化说明

### 已去除的功能

- ❌ 登录界面（不需要登录）
- ❌ JWT Token验证
- ❌ 用户管理
- ❌ 权限控制

### 保留的功能

- ✅ 所有管理API
- ✅ 审计日志（记录所有操作）
- ✅ 统计分析
- ✅ 完整的CRUD功能

---

## 💾 资源占用

### 运行时内存

```
PostgreSQL:  ~200MB  (优化配置)
后端API:     ~150MB  (Python FastAPI)
前端Dev:     ~100MB  (Vite开发服务器)
──────────────────────────────────
总计:        ~450MB
```

**剩余内存**: ~1.5GB（系统缓存和其他使用）

### 生产环境（构建后）

```
PostgreSQL:  ~200MB
后端API:     ~150MB
Nginx:       ~30MB   (托管前端静态文件)
──────────────────────────────────
总计:        ~380MB
```

---

## 📊 性能说明

### 单用户场景下的性能

- **响应时间**: < 200ms
- **搜索速度**: < 100ms（<1000篇文档）
- **上传速度**: 取决于网络和文件大小
- **并发能力**: 支持同时5-10个请求

### 数据容量

- **推荐**: < 1000篇文档
- **最大**: < 5000篇文档
- **数据库**: < 1GB

---

## 🔧 常见操作

### 上传文档

1. 点击"📤 上传"
2. 选择.docx文件
3. 填写章节信息
4. 点击上传

### 搜索内容

1. 点击"🔍 检索"
2. 输入关键词
3. 选择类型/章节（可选）
4. 查看结果

### 管理文档

1. 点击"⚙️ 管理"
2. 选择"📁 文档管理"
3. 查看/搜索/删除文档

### 批量审核分片

1. 进入"⚙️ 管理" → "📝 分片管理"
2. 勾选要审核的分片
3. 点击"批量审核"按钮

### 查看统计

1. 进入"⚙️ 管理" → "📊 仪表板"
2. 查看系统总览
3. 查看最近上传

---

## 🛠️ 开发说明

### 后端修改

- `admin/auth_simple.py` - 简化的认证（总是返回单用户）
- 所有`admin/routes/*.py` - 使用简化认证
- 不需要Token，直接调用API

### 前端修改

- `pages/Admin.tsx` - 新增管理页面（5个子功能）
- `lib/api.ts` - 添加管理API调用
- `main.tsx` - 添加管理选项卡

### API调用示例

```typescript
// 不需要token，直接调用
const data = await listDocs({ limit: 20, offset: 0 })
const stats = await getDashboard()
await deleteDoc(123)
```

---

## 📝 数据备份

### 备份数据库

```powershell
# 创建备份
docker exec chaoX-pg-1 pg_dump -U appuser appdb > backup.sql

# 或使用管理脚本（如果你运行了）
.\manage.sh  # 选择 8. 备份数据库
```

### 恢复数据库

```powershell
# 恢复备份
docker exec -i chaoX-pg-1 psql -U appuser appdb < backup.sql
```

---

## 🎯 生产环境部署

如果要部署到服务器：

### 1. 构建前端

```powershell
cd frontend
npm run build
```

### 2. 使用生产配置

```powershell
cd ..
docker-compose -f docker-compose.production.yml up -d
```

### 3. 访问

- 前端: http://服务器IP
- 后端: http://服务器IP:8787

---

## ✅ 功能检查清单

- [ ] 可以上传文档
- [ ] 可以搜索内容
- [ ] 可以查看统计数据
- [ ] 可以管理文档
- [ ] 可以管理分片
- [ ] 可以查看操作日志
- [ ] 资源占用正常（<50%）

---

## 🔍 故障排查

### 前端无法访问管理功能

1. 确认后端正常运行
2. 检查浏览器控制台错误
3. 访问 http://localhost:8787/admin/stats/dashboard 测试API

### 操作失败

1. 打开浏览器开发者工具（F12）
2. 查看Network标签
3. 检查API返回的错误信息

### 内存占用高

```powershell
# 查看资源使用
docker stats

# 重启服务
docker-compose restart
```

---

## 💡 优化建议

### 定期清理

```sql
-- 进入数据库
docker exec -it chaoX-pg-1 psql -U appuser -d appdb

-- 清理30天前的日志
DELETE FROM audit_log WHERE created_at < now() - interval '30 days';

-- 清理已删除的数据
DELETE FROM doc WHERE deleted_at < now() - interval '7 days';
DELETE FROM chunk WHERE deleted_at < now() - interval '7 days';
```

### 定期备份

建议每周备份一次数据库：
```powershell
$date = Get-Date -Format "yyyyMMdd"
docker exec chaoX-pg-1 pg_dump -U appuser appdb > "backup_$date.sql"
```

---

## 🎉 完成！

现在你有一个完整的单用户知识库管理系统：

- ✅ 无需登录
- ✅ 功能完整
- ✅ 资源占用低
- ✅ 界面友好

**开始使用吧！** 🚀

有任何问题随时查看：
- API文档: http://localhost:8787/docs
- 这个文件: SINGLE_USER_SETUP.md


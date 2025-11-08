# 🔧 故障排查指南

## 问题：知识检索和系统管理一直加载

### 快速诊断步骤

#### 1. 检查后端是否运行

```powershell
# 在浏览器访问
http://localhost:8787/health
```

**应该看到：**
```json
{"ok": true}
```

如果看不到，说明后端没运行。

---

#### 2. 检查管理系统API

```powershell
# 在浏览器访问
http://localhost:8787/admin/health
```

**应该看到：**
```json
{"ok": true, "service": "admin", "status": "running"}
```

---

#### 3. 使用API测试页面

打开文件：`frontend/test-api.html`

用浏览器直接打开这个文件，它会自动测试所有API。

---

#### 4. 检查浏览器控制台

1. 打开前端页面：http://localhost:5173
2. 按 F12 打开开发者工具
3. 点击"Console"（控制台）标签
4. 查看是否有红色错误信息

**常见错误：**

##### 错误1: `Network Error` 或 `ERR_CONNECTION_REFUSED`
**原因：** 后端未运行或端口错误

**解决：**
```powershell
cd C:\Users\exo32\Desktop\chaoxAI\chaoX\backend
.\start.ps1
```

##### 错误2: `404 Not Found`
**原因：** API路径错误

**解决：** 重启后端

##### 错误3: `500 Internal Server Error`
**原因：** 后端代码有错误

**解决：** 查看后端终端的错误信息

---

### 完整重启流程

如果以上都不行，完整重启：

```powershell
# 1. 停止所有服务
# 按 Ctrl+C 停止前端和后端

# 2. 重启数据库
cd C:\Users\exo32\Desktop\chaoxAI\chaoX
docker-compose restart pg

# 3. 等待10秒
Start-Sleep -Seconds 10

# 4. 启动后端
cd backend
.\start.ps1

# 5. 等待看到 "Application startup complete"

# 6. 新窗口启动前端
cd ..\frontend
npm run dev
```

---

### 测试数据库连接

```powershell
# 进入数据库
docker exec -it chaoX-pg-1 psql -U appuser -d appdb

# 检查表是否存在
\dt

# 查看doc表数据
SELECT COUNT(*) FROM doc;

# 查看chunk表数据
SELECT COUNT(*) FROM chunk;

# 退出
\q
```

**如果表不存在：**
```powershell
cd C:\Users\exo32\Desktop\chaoxAI\chaoX\backend
.\init-db.ps1
```

---

### 检查后端日志

后端终端应该显示：

```
INFO:     Uvicorn running on http://127.0.0.1:8787
INFO:     Application startup complete.
✓ 管理系统数据库初始化完成
```

**如果看到错误：**
- 复制错误信息
- 检查是否是导入错误
- 确认所有文件都已更新

---

### 前端问题排查

#### 清除缓存

```powershell
# 删除node_modules重新安装
cd C:\Users\exo32\Desktop\chaoxAI\chaoX\frontend
Remove-Item -Recurse -Force node_modules
npm install
npm run dev
```

#### 强制刷新浏览器

- 按 `Ctrl + Shift + R`
- 或 `Ctrl + F5`

---

### API测试命令

#### PowerShell测试

```powershell
# 测试健康检查
Invoke-RestMethod -Uri "http://localhost:8787/health"

# 测试搜索
Invoke-RestMethod -Uri "http://localhost:8787/search?limit=5"

# 测试管理API
Invoke-RestMethod -Uri "http://localhost:8787/admin/stats/system"
```

#### Curl测试（如果安装了curl）

```bash
curl http://localhost:8787/health
curl http://localhost:8787/admin/health
curl http://localhost:8787/search?limit=5
```

---

### 常见原因总结

| 症状 | 原因 | 解决方案 |
|------|------|---------|
| 一直加载 | 后端未运行 | 启动后端 |
| 404错误 | API路径错误 | 检查后端路由 |
| 500错误 | 后端代码错误 | 查看后端日志 |
| CORS错误 | 跨域问题 | 后端已配置，重启试试 |
| 空数据 | 数据库无数据 | 先上传一些文档 |

---

### 最简单的验证方法

1. **后端测试：** 浏览器打开 http://localhost:8787/docs
   - 如果能看到Swagger文档页面 = 后端正常 ✅
   
2. **前端测试：** 打开 http://localhost:5173
   - 如果能看到界面 = 前端正常 ✅

3. **数据测试：** 上传一个文档
   - 如果上传成功 = 整个流程正常 ✅

---

### 如果还是不行

提供以下信息：

1. **后端终端的完整输出**
2. **浏览器控制台的错误信息**（F12 → Console）
3. **访问 http://localhost:8787/health 的结果**
4. **数据库表列表**（`docker exec chaoX-pg-1 psql -U appuser -d appdb -c "\dt"`）

---

### 重置整个系统（最后手段）

⚠️ **会删除所有数据！**

```powershell
# 1. 停止所有服务
cd C:\Users\exo32\Desktop\chaoxAI\chaoX
docker-compose down

# 2. 删除数据（可选）
# Remove-Item -Recurse -Force data/pg

# 3. 重新启动
docker-compose up -d pg
Start-Sleep -Seconds 15

# 4. 初始化数据库
cd backend
.\init-db.ps1

# 5. 启动服务
.\start.ps1
```

---

## 快速检查清单

- [ ] 数据库运行中（`docker ps`）
- [ ] 后端运行中（看到 "Application startup complete"）
- [ ] 前端运行中（`npm run dev`）
- [ ] http://localhost:8787/health 返回 ok
- [ ] http://localhost:8787/admin/health 返回 ok
- [ ] 浏览器控制台无错误（F12）
- [ ] 数据库表已创建（图2显示的表都在）

全部打勾 = 应该能正常使用 ✅


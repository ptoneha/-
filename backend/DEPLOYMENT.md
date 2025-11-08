# 管理系统部署指南

## 🚀 部署步骤

### 1. 使用Docker Compose部署（推荐）

#### 1.1 确保Docker环境正常

```bash
docker --version
docker-compose --version
```

#### 1.2 启动服务

```bash
cd chaoX
docker-compose up -d
```

服务会自动初始化管理系统数据库。

#### 1.3 查看日志

```bash
docker-compose logs -f backend
```

#### 1.4 访问服务

- 后端API: http://localhost:8787
- API文档: http://localhost:8787/docs
- 管理API: http://localhost:8787/admin/
- 健康检查: http://localhost:8787/admin/health

---

### 2. 本地开发部署

#### 2.1 安装依赖

```bash
cd chaoX/backend

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境 (Windows)
.\.venv\Scripts\Activate.ps1

# 或者 (Linux/Mac)
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

#### 2.2 配置环境变量

创建 `.env` 文件：

```bash
# 数据库连接
DATABASE_URL=postgresql://appuser:123456@localhost:5432/appdb

# JWT密钥（生产环境必须修改）
JWT_SECRET_KEY=your-super-secret-key-change-me

# Token过期时间（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

#### 2.3 启动PostgreSQL

```bash
# 如果使用Docker
docker-compose up -d pg
```

#### 2.4 运行后端

```bash
uvicorn app:app --reload --port 8787
```

---

### 3. 生产环境部署

#### 3.1 更新Dockerfile（如需要）

```dockerfile
# chaoX/backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 环境变量
ENV DATABASE_URL=postgresql://appuser:123456@pg:5432/appdb
ENV JWT_SECRET_KEY=CHANGE_THIS_IN_PRODUCTION

# 暴露端口
EXPOSE 8787

# 启动命令
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8787"]
```

#### 3.2 更新docker-compose.yml

```yaml
version: '3.8'

services:
  pg:
    image: postgres:15
    environment:
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: 123456
      POSTGRES_DB: appdb
    volumes:
      - ./data/pg:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  backend:
    build: ./backend
    ports:
      - "8787:8787"
    environment:
      DATABASE_URL: postgresql://appuser:123456@pg:5432/appdb
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:-change-in-production}
    depends_on:
      - pg
    restart: unless-stopped
    volumes:
      - ./backend/static:/app/static
```

#### 3.3 设置环境变量

创建 `.env` 文件（不要提交到Git）：

```bash
JWT_SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=postgresql://appuser:STRONG_PASSWORD@pg:5432/appdb
```

#### 3.4 启动服务

```bash
docker-compose up -d --build
```

---

## 🔐 安全配置

### 1. 修改默认密码

启动后立即登录并修改管理员密码：

```bash
curl -X POST http://localhost:8787/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 获取token后修改密码
curl -X POST http://localhost:8787/admin/auth/change-password \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"old_password":"admin123","new_password":"NEW_STRONG_PASSWORD"}'
```

### 2. 生成强密码JWT密钥

```bash
# Linux/Mac
openssl rand -hex 32

# Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. 配置HTTPS（生产环境）

使用Nginx反向代理：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8787;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. 限制IP访问（可选）

在Nginx中限制管理后台访问：

```nginx
location /admin/ {
    allow 192.168.1.0/24;  # 允许内网
    deny all;               # 拒绝其他
    
    proxy_pass http://localhost:8787;
}
```

---

## 📊 监控与维护

### 1. 健康检查

```bash
# 检查服务状态
curl http://localhost:8787/health
curl http://localhost:8787/admin/health
```

### 2. 查看日志

```bash
# Docker日志
docker-compose logs -f backend

# 应用日志
tail -f /path/to/app.log
```

### 3. 数据库备份

```bash
# 备份数据库
docker exec -t postgres pg_dump -U appuser appdb > backup_$(date +%Y%m%d).sql

# 恢复数据库
docker exec -i postgres psql -U appuser appdb < backup_20231201.sql
```

### 4. 定期清理审计日志

```sql
-- 删除30天前的审计日志
DELETE FROM public.audit_log 
WHERE created_at < now() - interval '30 days';
```

---

## 🔧 故障排查

### 问题1: 无法连接数据库

**症状：** `could not connect to server`

**解决方案：**
1. 检查PostgreSQL是否运行：`docker-compose ps`
2. 检查连接字符串是否正确
3. 检查网络连接：`docker network ls`

### 问题2: Token验证失败

**症状：** `401 Unauthorized`

**解决方案：**
1. 检查JWT_SECRET_KEY是否一致
2. 确认Token未过期
3. 检查Authorization Header格式：`Bearer <token>`

### 问题3: 管理系统表不存在

**症状：** `relation "admin_user" does not exist`

**解决方案：**
```bash
# 手动执行SQL初始化
docker exec -i postgres psql -U appuser appdb < backend/admin_schema.sql
```

### 问题4: 性能问题

**解决方案：**
1. 检查数据库索引：
```sql
SELECT * FROM pg_stat_user_indexes;
```

2. 分析慢查询：
```sql
SELECT * FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 10;
```

3. 增加数据库连接池：修改 `db.py` 中的 `maxconn`

---

## 📈 性能优化

### 1. 数据库优化

```sql
-- 定期执行VACUUM
VACUUM ANALYZE;

-- 重建索引
REINDEX DATABASE appdb;
```

### 2. 应用优化

```python
# 在 db.py 中增加连接池大小
_pool = SimpleConnectionPool(minconn=5, maxconn=20, dsn=get_database_url())
```

### 3. 缓存策略（可选）

使用Redis缓存热数据：

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

---

## 🔄 更新升级

### 1. 更新代码

```bash
git pull origin main
```

### 2. 更新依赖

```bash
pip install -r requirements.txt --upgrade
```

### 3. 迁移数据库

如果有新的表或字段，运行SQL迁移脚本。

### 4. 重启服务

```bash
docker-compose restart backend
```

---

## 📞 技术支持

遇到问题？
1. 查看日志文件
2. 检查 [ADMIN_GUIDE.md](./ADMIN_GUIDE.md)
3. 查看API文档：http://localhost:8787/docs
4. 检查审计日志：查看管理后台操作记录

---

## ✅ 部署检查清单

- [ ] PostgreSQL正常运行
- [ ] 后端服务正常启动
- [ ] 可以访问 /health 端点
- [ ] 管理系统表已创建
- [ ] 默认管理员可以登录
- [ ] 已修改默认密码
- [ ] JWT_SECRET_KEY已配置
- [ ] 数据库连接正常
- [ ] 审计日志正常记录
- [ ] API文档可访问
- [ ] 已配置定期备份
- [ ] 已配置HTTPS（生产环境）
- [ ] 已限制管理后台访问IP（可选）

完成以上检查后，系统即可正常使用！


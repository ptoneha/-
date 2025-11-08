# 分片知识库上传与检索（chaoX）

在本目录内运行：网页上传 .docx → 后端解析分片 → 写入 PostgreSQL(5432) → 网页检索与预览（KaTeX）。

## 启动（Docker）
```
# 位于 chaoX 目录内
docker compose up -d            # 启动 pg(5432) + backend(8787)

# 前端（本地静态服务）
cd frontend
npm i
npm run build
npx serve -s dist -l 5173
```

- 后端：`http://localhost:8787`
- 前端：`http://localhost:5173`
- 数据库：宿主 `5432`（服务名 pg，密码 123456）

## 本地开发（使用虚拟环境）
```
# backend
cd backend

# 创建并激活虚拟环境（Windows PowerShell）
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt

# （可选）若 PowerShell 阻止脚本执行：
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 配置本地 .env（见 backend/.env.example）
# DATABASE_URL=postgresql://appuser:123456@localhost:5432/appdb

# 运行后端
uvicorn app:app --reload --port 8787

# frontend
cd ../frontend
npm i
npm run dev
```

## 说明
- 复用当前 chaoX 的 Postgres 数据卷（`./data/pg`），使用 5432 端口。
- 后端默认连接串（容器内）：`postgresql://appuser:123456@pg:5432/appdb`。
- 本地虚拟环境运行时，请在 backend/.env 中设置：`postgresql://appuser:123456@localhost:5432/appdb`。
- 上传只接收 `.docx` ≤ 10MB；H1/H2 解析、软切分片、去重与关键字分类均已实现。

# ChaoX 后端启动脚本
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ChaoX 知识库后端启动" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 检查虚拟环境
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "✓ 激活虚拟环境..." -ForegroundColor Green
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠ 虚拟环境不存在，创建中..." -ForegroundColor Yellow
    python -m venv .venv
    & .\.venv\Scripts\Activate.ps1
    Write-Host "✓ 虚拟环境创建完成" -ForegroundColor Green
}

# 检查依赖
Write-Host ""
Write-Host "检查依赖..." -ForegroundColor Cyan
pip show fastapi > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠ 安装依赖中..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "✓ 依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "✓ 依赖已安装" -ForegroundColor Green
}

# 启动服务
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  启动FastAPI服务..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "访问地址:" -ForegroundColor Cyan
Write-Host "  - API文档: http://localhost:8787/docs" -ForegroundColor Yellow
Write-Host "  - 管理后台: http://localhost:8787/admin/" -ForegroundColor Yellow
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Gray
Write-Host ""

uvicorn app:app --reload --port 8787


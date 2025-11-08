# ChaoX 数据库手动初始化脚本 (PowerShell)

Write-Host "========================================" -ForegroundColor Green
Write-Host "  ChaoX 管理系统 - 数据库初始化" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# 检查SQL文件
$sqlFile = "admin_schema_fixed.sql"
if (-not (Test-Path $sqlFile)) {
    $sqlFile = "admin_schema.sql"
}

if (-not (Test-Path $sqlFile)) {
    Write-Host "✗ 找不到SQL文件" -ForegroundColor Red
    exit 1
}

Write-Host "使用SQL文件: $sqlFile" -ForegroundColor Cyan
Write-Host ""

# 方式1: 使用Docker执行（推荐）
Write-Host "方式1: 通过Docker容器执行" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Gray
$dockerCmd = "docker exec -i chaoX-pg-1 psql -U appuser -d appdb < $sqlFile"
Write-Host $dockerCmd -ForegroundColor Gray
Write-Host ""
Write-Host "执行中..." -ForegroundColor Cyan

# 读取SQL文件内容并通过管道传递给docker
Get-Content $sqlFile | docker exec -i chaoX-pg-1 psql -U appuser -d appdb

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ 数据库初始化成功！" -ForegroundColor Green
    Write-Host ""
    
    # 验证表
    Write-Host "验证表创建..." -ForegroundColor Cyan
    docker exec chaoX-pg-1 psql -U appuser -d appdb -c "\dt public.admin_user"
    docker exec chaoX-pg-1 psql -U appuser -d appdb -c "SELECT COUNT(*) FROM admin_user;"
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  初始化完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "默认管理员账号:" -ForegroundColor Yellow
    Write-Host "  用户名: admin" -ForegroundColor White
    Write-Host "  密码: admin123" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "✗ 初始化失败" -ForegroundColor Red
    Write-Host ""
    Write-Host "可选方案:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "方式2: 使用Python脚本" -ForegroundColor Yellow
    Write-Host "  python init_db_manual.py" -ForegroundColor Gray
    Write-Host ""
    Write-Host "方式3: 手动执行SQL" -ForegroundColor Yellow
    Write-Host "  docker exec -i chaoX-pg-1 psql -U appuser -d appdb < $sqlFile" -ForegroundColor Gray
    exit 1
}


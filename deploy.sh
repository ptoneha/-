#!/bin/bash
# ChaoX 一键部署脚本（单用户优化版）

set -e

echo "================================================"
echo "   ChaoX 知识库管理系统 - 一键部署"
echo "================================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then 
    echo -e "${YELLOW}警告: 不建议使用root用户运行${NC}"
    read -p "是否继续？(y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 1. 检查系统资源
echo "📊 1. 检查系统资源..."
TOTAL_MEM=$(free -m | awk 'NR==2{print $2}')
if [ $TOTAL_MEM -lt 1800 ]; then
    echo -e "${RED}❌ 内存不足2GB，建议添加swap${NC}"
    read -p "是否自动创建2GB swap？(Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "创建swap..."
        sudo fallocate -l 2G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
        sudo sysctl vm.swappiness=10
        echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
        echo -e "${GREEN}✅ Swap创建成功${NC}"
    fi
else
    echo -e "${GREEN}✅ 内存充足 (${TOTAL_MEM}MB)${NC}"
fi

# 检查swap
SWAP=$(free -m | awk 'NR==3{print $2}')
if [ $SWAP -gt 0 ]; then
    echo -e "${GREEN}✅ Swap已启用 (${SWAP}MB)${NC}"
else
    echo -e "${YELLOW}⚠️  未启用swap，建议启用${NC}"
fi

# 2. 检查Docker
echo ""
echo "🐳 2. 检查Docker..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker未安装${NC}"
    echo "请先安装Docker: https://docs.docker.com/engine/install/"
    exit 1
fi
echo -e "${GREEN}✅ Docker已安装: $(docker --version)${NC}"

if ! command -v docker-compose &> /dev/null; then
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose未安装${NC}"
        exit 1
    fi
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi
echo -e "${GREEN}✅ Docker Compose已安装${NC}"

# 3. 配置环境变量
echo ""
echo "🔑 3. 配置环境变量..."
if [ ! -f .env ]; then
    echo "创建.env文件..."
    cp .env.example .env
    
    # 生成随机JWT密钥
    if command -v openssl &> /dev/null; then
        JWT_KEY=$(openssl rand -hex 32)
        sed -i "s/PLEASE_CHANGE_THIS_TO_A_RANDOM_STRING/$JWT_KEY/" .env
        echo -e "${GREEN}✅ 已生成随机JWT密钥${NC}"
    else
        echo -e "${YELLOW}⚠️  请手动修改.env中的JWT_SECRET_KEY${NC}"
    fi
    
    # 生成随机数据库密码
    DB_PASS=$(< /dev/urandom tr -dc A-Za-z0-9 | head -c32)
    sed -i "s/chaox123456/$DB_PASS/" .env
    echo -e "${GREEN}✅ 已生成随机数据库密码${NC}"
else
    echo -e "${GREEN}✅ .env文件已存在${NC}"
fi

# 4. 创建必要的目录
echo ""
echo "📁 4. 创建数据目录..."
mkdir -p data/pg
mkdir -p backend/static/qimg
echo -e "${GREEN}✅ 目录创建完成${NC}"

# 5. 构建前端（如果存在）
if [ -d "frontend" ]; then
    echo ""
    echo "🎨 5. 检查前端构建..."
    if [ ! -d "frontend/dist" ]; then
        echo "前端未构建，需要先构建前端..."
        if [ -f "frontend/package.json" ]; then
            cd frontend
            echo "安装依赖..."
            npm install
            echo "构建前端..."
            npm run build
            cd ..
            echo -e "${GREEN}✅ 前端构建完成${NC}"
        else
            echo -e "${YELLOW}⚠️  前端源码不完整，跳过${NC}"
        fi
    else
        echo -e "${GREEN}✅ 前端已构建${NC}"
    fi
fi

# 6. 启动服务
echo ""
echo "🚀 6. 启动Docker服务..."
echo "使用配置文件: docker-compose.production.yml"
$COMPOSE_CMD -f docker-compose.production.yml down 2>/dev/null || true
$COMPOSE_CMD -f docker-compose.production.yml up -d --build

# 7. 等待服务启动
echo ""
echo "⏳ 等待服务启动..."
sleep 10

# 8. 检查服务状态
echo ""
echo "📋 8. 检查服务状态..."
$COMPOSE_CMD -f docker-compose.production.yml ps

# 9. 健康检查
echo ""
echo "🏥 9. 健康检查..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -sf http://localhost:8787/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 后端服务正常${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "等待后端启动... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ 后端启动超时，请检查日志${NC}"
    $COMPOSE_CMD -f docker-compose.production.yml logs backend
    exit 1
fi

# 检查管理系统
if curl -sf http://localhost:8787/admin/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 管理系统正常${NC}"
else
    echo -e "${YELLOW}⚠️  管理系统可能未就绪${NC}"
fi

# 10. 显示访问信息
echo ""
echo "================================================"
echo -e "${GREEN}🎉 部署完成！${NC}"
echo "================================================"
echo ""
echo "📍 访问地址:"
echo "   - 前端: http://localhost"
echo "   - 后端API: http://localhost:8787"
echo "   - API文档: http://localhost:8787/docs"
echo "   - 管理后台: http://localhost:8787/admin/"
echo ""
echo "🔐 默认管理员账号:"
echo "   用户名: admin"
echo "   密码: admin123"
echo "   ⚠️  请立即登录修改密码！"
echo ""
echo "📊 查看资源使用:"
echo "   docker stats"
echo ""
echo "📋 查看日志:"
echo "   $COMPOSE_CMD -f docker-compose.production.yml logs -f backend"
echo ""
echo "🔄 重启服务:"
echo "   $COMPOSE_CMD -f docker-compose.production.yml restart"
echo ""
echo "🛑 停止服务:"
echo "   $COMPOSE_CMD -f docker-compose.production.yml down"
echo ""
echo "================================================"
echo ""

# 11. 测试登录
echo "🧪 测试管理员登录..."
LOGIN_RESULT=$(curl -s -X POST http://localhost:8787/admin/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"admin123"}')

if echo "$LOGIN_RESULT" | grep -q "access_token"; then
    echo -e "${GREEN}✅ 登录测试成功${NC}"
    echo ""
    echo "获取Token命令:"
    echo "curl -X POST http://localhost:8787/admin/auth/login \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"username\":\"admin\",\"password\":\"admin123\"}'"
else
    echo -e "${YELLOW}⚠️  登录测试失败，可能需要等待数据库初始化${NC}"
    echo "请等待1-2分钟后重试"
fi

echo ""
echo "📚 更多文档:"
echo "   - 使用指南: backend/ADMIN_GUIDE.md"
echo "   - 快速开始: QUICKSTART.md"
echo ""


#!/bin/bash
# ChaoX 管理脚本

COMPOSE_FILE="docker-compose.production.yml"
COMPOSE_CMD="docker-compose"

# 检查docker compose命令
if ! command -v docker-compose &> /dev/null; then
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    fi
fi

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

show_menu() {
    echo "================================================"
    echo "   ChaoX 管理菜单"
    echo "================================================"
    echo ""
    echo "1. 启动服务"
    echo "2. 停止服务"
    echo "3. 重启服务"
    echo "4. 查看状态"
    echo "5. 查看日志"
    echo "6. 查看资源使用"
    echo "7. 进入数据库"
    echo "8. 备份数据库"
    echo "9. 清理审计日志（30天前）"
    echo "10. 修改管理员密码"
    echo "0. 退出"
    echo ""
}

start_service() {
    echo -e "${GREEN}启动服务...${NC}"
    $COMPOSE_CMD -f $COMPOSE_FILE up -d
    echo -e "${GREEN}✅ 服务已启动${NC}"
}

stop_service() {
    echo -e "${YELLOW}停止服务...${NC}"
    $COMPOSE_CMD -f $COMPOSE_FILE down
    echo -e "${GREEN}✅ 服务已停止${NC}"
}

restart_service() {
    echo -e "${YELLOW}重启服务...${NC}"
    $COMPOSE_CMD -f $COMPOSE_FILE restart
    echo -e "${GREEN}✅ 服务已重启${NC}"
}

show_status() {
    echo -e "${GREEN}服务状态:${NC}"
    $COMPOSE_CMD -f $COMPOSE_FILE ps
    echo ""
    echo -e "${GREEN}健康检查:${NC}"
    curl -s http://localhost:8787/health | jq '.' || echo "后端未响应"
    curl -s http://localhost:8787/admin/health | jq '.' || echo "管理系统未响应"
}

show_logs() {
    echo "选择要查看的日志:"
    echo "1. 后端日志"
    echo "2. 数据库日志"
    echo "3. Nginx日志"
    echo "4. 全部日志"
    read -p "请选择 [1-4]: " log_choice
    
    case $log_choice in
        1) $COMPOSE_CMD -f $COMPOSE_FILE logs -f backend ;;
        2) $COMPOSE_CMD -f $COMPOSE_FILE logs -f pg ;;
        3) $COMPOSE_CMD -f $COMPOSE_FILE logs -f nginx ;;
        4) $COMPOSE_CMD -f $COMPOSE_FILE logs -f ;;
        *) echo "无效选择" ;;
    esac
}

show_stats() {
    echo -e "${GREEN}资源使用统计:${NC}"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
    echo ""
    echo -e "${GREEN}内存使用:${NC}"
    free -h
    echo ""
    echo -e "${GREEN}磁盘使用:${NC}"
    df -h . | grep -v "Filesystem"
}

enter_db() {
    echo -e "${GREEN}进入PostgreSQL...${NC}"
    docker exec -it chaoX-postgres psql -U appuser -d appdb
}

backup_db() {
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    echo -e "${GREEN}备份数据库到: $BACKUP_FILE${NC}"
    docker exec chaoX-postgres pg_dump -U appuser appdb > $BACKUP_FILE
    echo -e "${GREEN}✅ 备份完成${NC}"
    ls -lh $BACKUP_FILE
}

clean_logs() {
    echo -e "${YELLOW}清理30天前的审计日志...${NC}"
    read -p "确认清理？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker exec chaoX-postgres psql -U appuser -d appdb -c \
            "DELETE FROM audit_log WHERE created_at < now() - interval '30 days';"
        echo -e "${GREEN}✅ 清理完成${NC}"
    fi
}

change_password() {
    echo -e "${GREEN}修改管理员密码${NC}"
    echo ""
    read -p "请输入用户名 [admin]: " username
    username=${username:-admin}
    
    # 先登录获取token
    echo "正在登录..."
    read -sp "请输入旧密码: " old_pass
    echo ""
    
    TOKEN=$(curl -s -X POST http://localhost:8787/admin/auth/login \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$username\",\"password\":\"$old_pass\"}" \
        | jq -r '.access_token')
    
    if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
        echo -e "${RED}❌ 登录失败，密码错误${NC}"
        return
    fi
    
    read -sp "请输入新密码: " new_pass
    echo ""
    read -sp "确认新密码: " new_pass2
    echo ""
    
    if [ "$new_pass" != "$new_pass2" ]; then
        echo -e "${RED}❌ 两次密码不一致${NC}"
        return
    fi
    
    RESULT=$(curl -s -X POST http://localhost:8787/admin/auth/change-password \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"old_password\":\"$old_pass\",\"new_password\":\"$new_pass\"}")
    
    if echo "$RESULT" | grep -q "ok.*true"; then
        echo -e "${GREEN}✅ 密码修改成功${NC}"
    else
        echo -e "${RED}❌ 密码修改失败${NC}"
        echo "$RESULT"
    fi
}

# 主循环
while true; do
    show_menu
    read -p "请选择操作 [0-10]: " choice
    echo ""
    
    case $choice in
        1) start_service ;;
        2) stop_service ;;
        3) restart_service ;;
        4) show_status ;;
        5) show_logs ;;
        6) show_stats ;;
        7) enter_db ;;
        8) backup_db ;;
        9) clean_logs ;;
        10) change_password ;;
        0) echo "再见！"; exit 0 ;;
        *) echo -e "${RED}无效选择${NC}" ;;
    esac
    
    echo ""
    read -p "按Enter继续..."
    clear
done


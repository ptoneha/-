"""管理系统数据库初始化"""
import os
from db import get_conn, release_conn, _execute


def init_admin_schema():
    """初始化管理系统数据库结构"""
    conn = get_conn()
    try:
        conn.autocommit = True
        
        # 读取SQL文件
        sql_file = os.path.join(os.path.dirname(__file__), "../admin_schema.sql")
        
        if not os.path.exists(sql_file):
            print(f"警告: 找不到 {sql_file}")
            return
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割并执行SQL语句
        statements = sql_content.split(';')
        
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    _execute(conn, statement)
                except Exception as e:
                    # 某些语句可能已经执行过，忽略错误
                    print(f"执行SQL时出错（可能已存在）: {str(e)[:100]}")
        
        print("✓ 管理系统数据库初始化完成")
        
    except Exception as e:
        print(f"✗ 管理系统数据库初始化失败: {e}")
    finally:
        release_conn(conn)


if __name__ == "__main__":
    init_admin_schema()


"""
数据库操作
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
import config


def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            department TEXT DEFAULT 'default',
            quota REAL DEFAULT 10.0,
            used_quota REAL DEFAULT 0.0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 调用日志表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            api_path TEXT NOT NULL,
            cost REAL NOT NULL,
            status_code INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    conn.commit()
    conn.close()


def create_user(name: str, email: str = "", department: str = "default", 
                quota: float = None) -> Dict[str, Any]:
    """创建新用户"""
    import secrets
    api_key = f"tk-{secrets.token_urlsafe(32)}"
    
    if quota is None:
        quota = config.DEFAULT_USER_QUOTA
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (api_key, name, email, department, quota)
        VALUES (?, ?, ?, ?, ?)
    """, (api_key, name, email, department, quota))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": user_id,
        "api_key": api_key,
        "name": name,
        "email": email,
        "department": department,
        "quota": quota,
        "used_quota": 0.0,
    }


def get_user_by_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """通过 API Key 获取用户"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE api_key = ? AND is_active = 1", (api_key,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """通过 ID 获取用户"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def list_users() -> List[Dict[str, Any]]:
    """列出所有用户"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def log_usage(user_id: int, api_path: str, cost: float, status_code: int = 200):
    """记录一次调用"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 记录日志
    cursor.execute("""
        INSERT INTO usage_logs (user_id, api_path, cost, status_code)
        VALUES (?, ?, ?, ?)
    """, (user_id, api_path, cost, status_code))
    
    # 扣减用户额度
    cursor.execute("""
        UPDATE users SET used_quota = used_quota + ? WHERE id = ?
    """, (cost, user_id))
    
    conn.commit()
    conn.close()


def get_daily_usage(date: str = None) -> List[Dict[str, Any]]:
    """
    获取某天的用量统计（按用户汇总）
    date 格式：YYYY-MM-DD
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            u.id as user_id,
            u.name,
            u.email,
            u.department,
            u.quota,
            u.used_quota,
            COUNT(l.id) as call_count,
            COALESCE(SUM(l.cost), 0) as total_cost
        FROM users u
        LEFT JOIN usage_logs l ON u.id = l.user_id 
            AND date(l.created_at) = date(?)
        GROUP BY u.id
        ORDER BY total_cost DESC
    """, (date,))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_api_usage_stats(date: str = None) -> List[Dict[str, Any]]:
    """获取某天按 API 路径的用量统计"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            api_path,
            COUNT(*) as call_count,
            COALESCE(SUM(cost), 0) as total_cost
        FROM usage_logs
        WHERE date(created_at) = date(?)
        GROUP BY api_path
        ORDER BY call_count DESC
    """, (date,))
    
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

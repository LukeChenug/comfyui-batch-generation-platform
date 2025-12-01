import sqlite3
import json
import logging
import uuid
import datetime
from typing import Dict, List, Optional, Any
from backend.src.config.settings import DB_PATH

logger = logging.getLogger(__name__)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. 创建 tasks 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            progress REAL DEFAULT 0,
            message TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            completed_at TEXT,
            result_url TEXT,
            result_urls TEXT,
            error TEXT,
            request_data TEXT,
            batch_name TEXT,
            user_id TEXT
        )
    ''')
    
    # 2. 创建 users 表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            api_key TEXT UNIQUE,
            role TEXT DEFAULT 'user',
            created_at TEXT,
            is_active BOOLEAN DEFAULT 1
        )
    ''')
    
    # 3. 数据库迁移：检查并添加字段
    try:
        # 检查 tasks 表是否需要迁移 result_urls
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'result_urls' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN result_urls TEXT")
            logger.info("已添加 result_urls 字段到 tasks 表")
            
        if 'user_id' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN user_id TEXT")
            logger.info("已添加 user_id 字段到 tasks 表")
            
            # 将现有任务归属给默认 admin (稍后创建)
            # 暂时先留空，等 admin 创建后再说
            
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
    
    conn.commit()
    conn.close()

# ================= 用户相关操作 =================

def create_user(username: str, role: str = 'user', api_key: str = None) -> Dict[str, Any]:
    """创建新用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    user_id = str(uuid.uuid4())
    if not api_key:
        api_key = f"sk-{uuid.uuid4().hex[:8]}"
    
    now = datetime.datetime.now().isoformat()
    
    try:
        cursor.execute('''
            INSERT INTO users (id, username, api_key, role, created_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, username, api_key, role, now, True))
        conn.commit()
        return {
            "id": user_id,
            "username": username,
            "api_key": api_key,
            "role": role,
            "created_at": now
        }
    except sqlite3.IntegrityError:
        # 用户名或Key已存在
        return None
    finally:
        conn.close()

def get_user_by_key(api_key: str) -> Optional[Dict[str, Any]]:
    """通过API Key获取用户"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE api_key = ? AND is_active = 1', (api_key,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_users() -> List[Dict[str, Any]]:
    """获取所有用户（管理员用）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, api_key, role, created_at, is_active FROM users ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# ================= 任务相关操作 =================

def save_task(task_data: Dict[str, Any]):
    """保存或更新任务"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 准备数据
    result_urls_json = json.dumps(task_data.get("result_urls")) if task_data.get("result_urls") else None
    request_data_json = json.dumps(task_data.get("request_data")) if isinstance(task_data.get("request_data"), dict) else task_data.get("request_data")
    
    # 检查是否存在
    cursor.execute("SELECT task_id FROM tasks WHERE task_id = ?", (task_data["task_id"],))
    exists = cursor.fetchone()
    
    if exists:
        cursor.execute('''
            UPDATE tasks SET 
                status=?, progress=?, message=?, completed_at=?, 
                result_url=?, error=?, result_urls=?
            WHERE task_id=?
        ''', (
            task_data.get("status"),
            task_data.get("progress"),
            task_data.get("message"),
            task_data.get("completed_at"),
            task_data.get("result_url"),
            task_data.get("error"),
            result_urls_json,
            task_data["task_id"]
        ))
    else:
        cursor.execute('''
            INSERT INTO tasks (
                task_id, status, progress, message, created_at, 
                request_data, batch_name, result_urls, user_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_data["task_id"],
            task_data.get("status", "pending"),
            task_data.get("progress", 0),
            task_data.get("message", ""),
            task_data.get("created_at"),
            request_data_json,
            task_data.get("batch_name"),
            result_urls_json,
            task_data.get("user_id")  # 新增 user_id
        ))
    
    conn.commit()
    conn.close()

def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """获取单个任务"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return _parse_row(row)

def get_tasks_by_user(user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """获取指定用户的任务"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM tasks 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (user_id, limit))
    
    rows = cursor.fetchall()
    conn.close()
    return [_parse_row(row) for row in rows]

def get_all_tasks_admin(limit: int = 100) -> List[Dict[str, Any]]:
    """获取所有任务（管理员用）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    return [_parse_row(row) for row in rows]

def _parse_row(row) -> Dict[str, Any]:
    """解析数据库行"""
    task = dict(row)
    
    # 解析JSON字段
    if task.get("result_urls"):
        try:
            task["result_urls"] = json.loads(task["result_urls"])
        except (json.JSONDecodeError, TypeError):
            pass
            
    if task.get("request_data"):
        try:
            task["request_data"] = json.loads(task["request_data"])
        except (json.JSONDecodeError, TypeError):
            pass
            
    return task

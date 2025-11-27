import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
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
            batch_name TEXT
        )
    ''')
    
    # 检查并添加result_urls字段（数据库迁移）
    try:
        cursor.execute("SELECT result_urls FROM tasks LIMIT 1")
    except sqlite3.OperationalError:
        # 字段不存在，添加它
        cursor.execute("ALTER TABLE tasks ADD COLUMN result_urls TEXT")
        conn.commit()
        logger.info("已添加result_urls字段到数据库")
    
    conn.commit()
    conn.close()

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
                request_data, batch_name, result_urls
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task_data["task_id"],
            task_data.get("status", "pending"),
            task_data.get("progress", 0),
            task_data.get("message", ""),
            task_data.get("created_at"),
            request_data_json,
            task_data.get("batch_name"),
            result_urls_json
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

def get_recent_tasks(limit: int = 100) -> List[Dict[str, Any]]:
    """获取最近的任务"""
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


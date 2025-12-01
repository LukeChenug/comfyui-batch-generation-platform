import logging
from backend.src.database.db import create_user, get_db_connection

logger = logging.getLogger(__name__)

def init_admin_account():
    """初始化默认管理员账号"""
    # 检查是否已有管理员
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, api_key FROM users WHERE role = 'admin' LIMIT 1")
    admin = cursor.fetchone()
    
    admin_id = None
    
    if not admin:
        logger.info("未找到管理员账号，正在创建默认管理员...")
        # 创建默认管理员
        # TODO: 在生产环境中，这些应该从环境变量读取
        default_key = "sk-admin-123456" 
        result = create_user("admin", "admin", default_key)
        
        if result:
            logger.info(f"✅ 管理员创建成功!")
            logger.info(f"   用户名: admin")
            logger.info(f"   API Key: {default_key}")
            admin_id = result["id"]
        else:
            logger.error("❌ 管理员创建失败")
            return
    else:
        admin_id = admin["id"]
        logger.info(f"✅ 管理员账号已存在 (ID: {admin_id})")
    
    # 数据迁移：将没有 user_id 的历史任务归属给管理员
    cursor.execute("SELECT count(*) FROM tasks WHERE user_id IS NULL")
    count = cursor.fetchone()[0]
    
    if count > 0 and admin_id:
        logger.info(f"正在将 {count} 个历史任务归属给管理员...")
        cursor.execute("UPDATE tasks SET user_id = ? WHERE user_id IS NULL", (admin_id,))
        conn.commit()
        logger.info("✅ 历史任务迁移完成")
    
    conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_admin_account()


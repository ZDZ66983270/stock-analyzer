import sqlite3
from config import DB_PATH

def get_connection():
    """返回 SQLite 连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化数据库"""
    conn = get_connection()
    with open("db/schema.sql", "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

from sqlmodel import SQLModel, create_engine, Session

import os

sqlite_file_name = "database.db"
# Use absolute path based on this file's location
base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, sqlite_file_name)
sqlite_url = f"sqlite:///{db_path}"

connect_args = {"check_same_thread": False}
engine = create_engine(
    sqlite_url, 
    echo=True, 
    connect_args=connect_args,
    pool_size=10,           # 连接池大小（从默认5增加到10）
    max_overflow=15,        # 超出pool_size的溢出连接数
    pool_timeout=30,        # 获取连接超时（秒）
    pool_recycle=3600       # 连接回收时间（秒，1小时）
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

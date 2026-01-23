
from sqlmodel import Session, select, delete
from backend.database import engine
from backend.models import MarketSnapshot

def clear_snapshot_data():
    """清除MarketSnapshot表中所有数据，以便验证重新获取"""
    with Session(engine) as session:
        # 直接清空Snapshot表，强迫系统重新获取最新快照
        # 用户提到"19日的行情数据"，snapshot只有最新一条
        # 所以直接清空Snapshot表是最彻底的验证方式
        statement = delete(MarketSnapshot)
        result = session.exec(statement)
        session.commit()
        print(f"✅ MarketSnapshot table cleared. {result.rowcount} records deleted.")

if __name__ == "__main__":
    clear_snapshot_data()

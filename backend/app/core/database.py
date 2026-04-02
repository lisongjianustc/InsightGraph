import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 从环境变量读取数据库配置
DB_USER = os.getenv("DB_USER", "insight_admin")
DB_PASS = os.getenv("DB_PASS", "insight_secure_pass_123")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "insight_graph_db")

# 本地调试时，如果没在 Docker 里，使用 localhost
if not os.getenv("DB_HOST"):
    DB_HOST = "localhost"

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

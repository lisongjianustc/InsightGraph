import os
import sys

from sqlalchemy import create_engine, text

# 本地调试时，如果没在 Docker 里，使用 localhost
DB_USER = os.getenv("DB_USER", "insight_admin")
DB_PASS = os.getenv("DB_PASS", "insight_secure_pass_123")
DB_HOST = os.getenv("DB_HOST", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "insight_graph_db")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE capsules ADD COLUMN IF NOT EXISTS file_url VARCHAR(500);"))
        conn.execute(text("ALTER TABLE capsules ADD COLUMN IF NOT EXISTS file_type VARCHAR(50);"))
        conn.commit()
    print("Migration successful.")
except Exception as e:
    print(f"Migration failed: {e}")

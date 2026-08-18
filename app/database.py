import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sql import CREATE_SQL_TABLES

load_dotenv()


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "food_delivery")

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)

SESSION_EXPIRE_SECONDS = int(
    os.getenv(
        "SESSION_EXPIRE_SECONDS",
        "86400",
    )
)

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
        
def create_tables():
    with engine.connect()as conn:
        for st in CREATE_SQL_TABLES.strip().strip(';'):
            stmt = st.strip()
            if stmt:
                conn.execte(text(stmt))
            conn.commit()
            
        print("All Tables Created (or already exist).")
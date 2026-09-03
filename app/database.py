import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from sql.schema import CREATE_SQL_TABLES

load_dotenv()


# =========================
# Database Configuration
# =========================

DB_HOST = os.getenv(
    "DB_HOST",
    "localhost"
)

DB_PORT = os.getenv(
    "DB_PORT",
    "3306"
)

DB_USER = os.getenv(
    "DB_USER",
    "root"
)

DB_PASSWORD = os.getenv(
    "DB_PASSWORD",
    ""
)

DB_NAME = os.getenv(
    "DB_NAME",
    "food_delivery_db"
)


# =========================
# Redis Configuration
# =========================

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0"
)

SESSION_EXPIRE_SECONDS = int(
    os.getenv(
        "SESSION_EXPIRE_SECONDS",
        "86400"
    )
)


# =========================
# MySQL Connection
# =========================

SERVER_DATABASE_URL = (
    f"mysql+pymysql://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}"
)


DATABASE_URL = (
    f"mysql+pymysql://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


# =========================
# Create Database
# =========================

def create_database():

    server_engine = create_engine(
        SERVER_DATABASE_URL,
        pool_pre_ping=True
    )

    try:

        with server_engine.connect() as conn:

            conn.execute(
                text(
                    f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`"
                )
            )

            conn.commit()

    finally:

        server_engine.dispose()


# Create database before connecting to it
create_database()


# =========================
# SQLAlchemy Engine
# =========================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# =========================
# Session
# =========================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)


Base = declarative_base()


# =========================
# Database Dependency
# =========================

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()


# =========================
# Create Tables
# =========================

def create_tables():

    statements = [
        statement.strip()
        for statement in CREATE_SQL_TABLES.split(";")
        if statement.strip()
    ]

    with engine.begin() as conn:

        for statement in statements:

            conn.execute(
                text(statement)
            )

    print(
        "All tables created successfully."
    )


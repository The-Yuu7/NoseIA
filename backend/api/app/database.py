import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger("E-Nose-Database")

DB_HOST = os.getenv("DB_HOST", "192.168.0.203")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "bioenose_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "change_me")

POSTGRES_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SQLITE_URL = "sqlite:///./enose_scada.db"

try:
    if os.getenv("USE_POSTGRES") == "true" or os.getenv("ENVIRONMENT") == "production":
        engine = create_engine(POSTGRES_URL, pool_pre_ping=True)
    else:
        engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
except Exception as err:
    logger.warning("PostgreSQL no disponible (%s). Usando SQLite local.", err)
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for obtaining database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from __future__ import annotations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..config import settings

engine = None
SessionLocal = None

def init_engine():
    global engine, SessionLocal
    if settings.MYSQL_URL:
        engine = create_engine(settings.MYSQL_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    else:
        engine = None
        SessionLocal = None
    return engine, SessionLocal

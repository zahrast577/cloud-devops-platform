"""Connexion à la base de données (SQLAlchemy)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

from .config import DATABASE_URL


class Base(DeclarativeBase):
    pass


connect_args = {}
engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Une base SQLite en mémoire doit partager une seule connexion (tests).
    if DATABASE_URL in ("sqlite://", "sqlite:///:memory:"):
        engine_kwargs["poolclass"] = StaticPool

# pool_pre_ping : vérifie qu'une connexion est vivante avant de l'utiliser
# (utile si PostgreSQL redémarre pendant que l'API tourne).
engine = create_engine(
    DATABASE_URL, pool_pre_ping=True, connect_args=connect_args, **engine_kwargs
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""Defined a database session"""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__)) 
SQLALCHEMY_DATABASE_URL = f"sqlite:///{BASE_DIR}/db.sqlite3"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# return database session class, we can create session instance to be a database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

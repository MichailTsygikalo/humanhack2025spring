from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import app_settings

engine = create_engine(app_settings.postgres_database_url)
SessionLocal = sessionmaker(engine, class_=Session, expire_on_commit=False)

def get_session():
    with SessionLocal() as session:
        yield session

class Base(DeclarativeBase): ...


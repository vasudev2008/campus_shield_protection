from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..core.config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    import app.models  # noqa: F401 - ensures models are imported
    Base.metadata.create_all(bind=engine)

# Dependency for FastAPI routes

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

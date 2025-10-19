from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 📌 Для SQLite используем файл app.db в корне
DATABASE_URL = "sqlite:///./app.db"

# connect_args нужен для SQLite
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def init_db():
    from app.models import User, Note, Event  # импортируем модели перед созданием таблиц
    Base.metadata.create_all(bind=engine)

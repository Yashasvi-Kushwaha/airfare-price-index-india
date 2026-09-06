from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base

engine = create_engine(
    "sqlite:///airfare_data.db",
    pool_size=10,
    max_overflow=20,
    pool_timeout=30
)
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)
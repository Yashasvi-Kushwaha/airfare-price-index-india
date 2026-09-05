from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base

engine = create_engine("sqlite:///airfare_data.db")
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(bind=engine)
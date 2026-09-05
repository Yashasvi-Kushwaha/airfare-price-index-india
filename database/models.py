from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class FareObservation(Base):
    __tablename__ = "flight_observations"

    id = Column(Integer, primary_key=True, autoincrement=True)

    source = Column(String, nullable=False)
    origin = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    travel_date = Column(String, nullable=False)
    collection_timestamp = Column(DateTime, nullable=False)
    advance_days = Column(Integer, nullable=False)

    airline = Column(String)
    flight_number = Column(String)
    departure_time = Column(String)

    cabin = Column(String, default="economy")
    fare_type = Column(String)

    base_fare = Column(Float, nullable=True)
    taxes = Column(Float, nullable=True)
    airport_charges = Column(Float, nullable=True)
    convenience_fee = Column(Float, nullable=True)
    baggage_fee = Column(Float, nullable=True)
    total_fare = Column(Float, nullable=False)

    currency = Column(String, default="INR")
    available = Column(Boolean, default=True)

    fare_breakdown_available = Column(Boolean, default=False)
    quality_status = Column(String, default="PENDING")
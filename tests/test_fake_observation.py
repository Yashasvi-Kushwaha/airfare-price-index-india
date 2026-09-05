import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from database.db_setup import SessionLocal
from database.models import FareObservation

session = SessionLocal()

fake_obs = FareObservation(
    source="test",
    origin="DEL",
    destination="BOM",
    travel_date="2026-09-12",
    collection_timestamp=datetime.now(),
    advance_days=7,
    airline="IndiGo",
    flight_number="6E2045",
    departure_time="10:30",
    cabin="economy",
    total_fare=4300,
    fare_breakdown_available=False,
    quality_status="VALID"
)

session.add(fake_obs)
session.commit()
print("Inserted fake observation with id:", fake_obs.id)
from database.db_setup import SessionLocal
from database.models import FareObservation


session = SessionLocal()

try:

    observations = session.query(
        FareObservation
    ).order_by(
        FareObservation.id.desc()
    ).limit(10).all()

    print("\nDATABASE CHECK")
    print("=" * 90)

    for obs in observations:

        print(
            f"ID: {obs.id} | "
            f"{obs.flight_number} | "
            f"{obs.origin}-{obs.destination} | "
            f"{obs.travel_date} | "
            f"{obs.fare_type} | "
            f"₹{obs.total_fare:,.2f}"
        )

    print("=" * 90)

    total = session.query(
        FareObservation
    ).count()

    print(f"Total records in database: {total}")

finally:

    session.close()
from database.db_setup import SessionLocal
from database.models import FareObservation
from scraper.flight_scraper import scrape_spicejet_fare


def save_observations(observations):

    session = SessionLocal()

    try:

        for obs in observations:

            record = FareObservation(
                source=obs["source"],
                origin=obs["origin"],
                destination=obs["destination"],
                travel_date=obs["travel_date"],
                collection_timestamp=__import__(
                    "datetime"
                ).datetime.fromisoformat(
                    obs["collection_timestamp"]
                ),
                advance_days=obs["advance_days"],

                airline="SpiceJet",
                flight_number=obs["flight_number"],
                departure_time=obs["departure_time"],

                cabin="economy",
                fare_type=obs["fare_type"],

                total_fare=obs["total_fare"],

                currency="INR",
                available=True,

                fare_breakdown_available=False,
                quality_status="VALID"
            )

            session.add(record)

        session.commit()

        print(
            f"\nSaved {len(observations)} "
            "observations to database."
        )

    except Exception as e:

        session.rollback()

        print(
            f"\nERROR while saving data: {e}"
        )

    finally:

        session.close()


if __name__ == "__main__":

    observations = scrape_spicejet_fare(
        origin_code="DEL",
        destination_code="BOM",
        advance_days=7
    )

    save_observations(observations)
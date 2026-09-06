import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import statistics
from database.db_setup import SessionLocal
from database.models import FareObservation


def get_observations_for_date(session, origin, destination, collection_date):
    """Fetch all VALID observations for a route on a specific collection date."""
    start = collection_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start.replace(hour=23, minute=59, second=59)

    return session.query(FareObservation).filter(
        FareObservation.origin == origin,
        FareObservation.destination == destination,
        FareObservation.collection_timestamp >= start,
        FareObservation.collection_timestamp <= end,
        FareObservation.quality_status == "VALID"
    ).all()


def daily_median_fare(observations):
    """Dashboard stat only — NOT used in the index calculation."""
    fares = [obs.total_fare for obs in observations]
    if not fares:
        return None
    return statistics.median(fares)


def daily_stats(observations):
    """Median, Q1, Q3 — dashboard statistics block."""
    fares = sorted([obs.total_fare for obs in observations])
    if not fares:
        return {"median": None, "q1": None, "q3": None, "n": 0}

    n = len(fares)
    median = statistics.median(fares)
    q1 = statistics.median(fares[:n // 2]) if n >= 2 else fares[0]
    q3 = statistics.median(fares[(n + 1) // 2:]) if n >= 2 else fares[0]

    return {"median": median, "q1": q1, "q3": q3, "n": n}


def jevons_movement(today_obs, yesterday_obs):
    """
    The actual index calculation.
    Matches observations by flight_number (same flight, consecutive days),
    computes each matched flight's price relative, takes the geometric mean.
    Returns None if no matched flights exist.
    Return dict always has keys: jevons_movement, matched_flights, relatives.
    """
    today_by_flight = {obs.flight_number: obs.total_fare for obs in today_obs}
    yesterday_by_flight = {obs.flight_number: obs.total_fare for obs in yesterday_obs}

    matched_flights = set(today_by_flight.keys()) & set(yesterday_by_flight.keys())

    if not matched_flights:
        return None

    relatives = [
        today_by_flight[f] / yesterday_by_flight[f]
        for f in matched_flights
        if yesterday_by_flight[f] > 0
    ]

    if not relatives:
        return None

    n = len(relatives)
    product = math.prod(relatives)
    jevons = (product ** (1 / n)) * 100

    return {
        "jevons_movement": jevons,
        "matched_flights": n,
        "relatives": relatives
    }


def chain_index(previous_index, jevons_movement_value):
    """Chains today's Jevons movement onto the running index."""
    if jevons_movement_value is None:
        return previous_index
    return previous_index * (jevons_movement_value / 100)


if __name__ == "__main__":
    from datetime import datetime, timedelta

    session = SessionLocal()

    origin, destination = "DEL", "BOM"
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    today_obs = get_observations_for_date(session, origin, destination, today)
    yesterday_obs = get_observations_for_date(session, origin, destination, yesterday)

    print(f"Today's observations: {len(today_obs)}")
    print(f"Yesterday's observations: {len(yesterday_obs)}")

    stats = daily_stats(today_obs)
    print(f"\nDashboard stats (today): {stats}")

    movement = jevons_movement(today_obs, yesterday_obs)
    print(f"\nJevons movement: {movement}")

    if movement:
        running_index = 100.0
        new_index = chain_index(running_index, movement["jevons_movement"])
        print(f"\nChained index: {new_index:.2f}")
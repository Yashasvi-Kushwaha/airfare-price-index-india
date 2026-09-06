from datetime import datetime, timedelta
import random


def generate_lead_time_observations(
    route_origin,
    route_dest,
    travel_date,
    base_fare,
    flight_pool=None,
    thin=False
):
    """
    Generate synthetic airfare observations for the SAME travel date
    at two different booking horizons: T+30 and T+7.

    This is synthetic data for MVP/demo/testing purposes.

    Important:
    - Same flight identity is maintained across T+30 and T+7.
    - Travel date remains fixed.
    - T+30 represents an earlier booking.
    - T+7 represents a later booking.
    """

    if flight_pool is None:
        if thin:
            flight_pool = [
                ("6E9001", "09:15"),
                ("6E9002", "18:30"),
            ]
        else:
            flight_pool = [
                ("6E2045", "10:30"),
                ("6E2134", "14:15"),
                ("AI865", "18:00"),
                ("6E711", "07:45"),
                ("6E901", "21:10"),
            ]

    observations = []

    # We intentionally make T+7 generally more expensive than T+30.
    # This is only synthetic demonstration data.
    for advance_days in [30, 7]:

        for flight_number, dep_time in flight_pool:

            if advance_days == 30:

                # Earlier booking → lower base price
                variation = random.randint(-250, 400)
                fare = base_fare + variation

            else:

                # Closer booking → higher price
                variation = random.randint(700, 2200)
                fare = base_fare + variation

                # Thin routes have larger volatility
                if thin:
                    fare += random.randint(0, 1800)

            airline = (
                "IndiGo"
                if flight_number.startswith("6E")
                else "Air India"
            )

            observations.append({
                "source": "sample_data",

                "origin": route_origin,
                "destination": route_dest,

                # SAME travel date for T+30 and T+7
                "travel_date": travel_date,

                "collection_timestamp": datetime.now(),

                "advance_days": advance_days,

                "airline": airline,
                "flight_number": flight_number,
                "departure_time": dep_time,

                "cabin": "economy",

                # Breakdown intentionally unavailable
                "base_fare": None,
                "taxes": None,
                "airport_charges": None,
                "convenience_fee": None,
                "baggage_fee": None,

                "total_fare": float(round(fare, 2)),

                "currency": "INR",

                "available": True,

                "fare_breakdown_available": False,

                "quality_status": "VALID"
            })

    return observations


def generate_daily_history(
    route_origin,
    route_dest,
    num_days=7,
    base_fare=5000,
    flight_pool=None,
    thin=False,
    advance_days=7
):
    """
    Generate historical daily observations for the existing
    daily index / median-history part of the dashboard.

    Unlike lead-time data, this function intentionally creates
    observations across different collection dates.
    """

    if flight_pool is None:
        if thin:
            flight_pool = [
                ("6E9001", "09:15"),
            ]
        else:
            flight_pool = [
                ("6E2045", "10:30"),
                ("6E2134", "14:15"),
                ("AI865", "18:00"),
            ]

    observations = []

    today = datetime.now()

    for day_offset in range(num_days):

        collection_date = today - timedelta(days=day_offset)

        for flight_number, dep_time in flight_pool:

            if thin:
                fare = base_fare + random.randint(-300, 2500)
            else:
                # Creates moderate day-to-day movement
                daily_change = random.randint(-250, 500)
                fare = base_fare + daily_change

            airline = (
                "IndiGo"
                if flight_number.startswith("6E")
                else "Air India"
            )

            observations.append({
                "source": "sample_data",

                "origin": route_origin,
                "destination": route_dest,

                "travel_date": (
                    collection_date + timedelta(days=advance_days)
                ).strftime("%Y-%m-%d"),

                "collection_timestamp": collection_date,

                "advance_days": advance_days,

                "airline": airline,
                "flight_number": flight_number,
                "departure_time": dep_time,

                "cabin": "economy",

                "base_fare": None,
                "taxes": None,
                "airport_charges": None,
                "convenience_fee": None,
                "baggage_fee": None,

                "total_fare": float(round(fare, 2)),

                "currency": "INR",

                "available": True,

                "fare_breakdown_available": False,

                "quality_status": "VALID"
            })

    return observations


if __name__ == "__main__":

    travel_date = (
        datetime.now() + timedelta(days=30)
    ).strftime("%Y-%m-%d")

    data = generate_lead_time_observations(
        "DEL",
        "BOM",
        travel_date,
        base_fare=4500,
        thin=False
    )

    print(f"Generated {len(data)} lead-time observations")

    for obs in data:
        print(
            obs["flight_number"],
            obs["advance_days"],
            obs["travel_date"],
            obs["total_fare"]
        )
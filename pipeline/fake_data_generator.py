from datetime import datetime, timedelta
import random

def generate_fake_observations(route_origin, route_dest, num_days=7, base_fare=4500,
                                 flight_pool=None, thin=False):
    """
    Generates realistic sample observations matching the FareObservation schema.
    day_offset=0 is always "today", going backward from there, so both
    today and yesterday reliably have full flight-pool coverage.
    """
    if flight_pool is None:
        if thin:
            flight_pool = [("6E9001", "09:15")]
        else:
            flight_pool = [
                ("6E2045", "10:30"),
                ("6E2134", "14:15"),
                ("AI865", "18:00"),
            ]

    observations = []

    for day_offset in range(num_days):
        collection_date = datetime.now() - timedelta(days=day_offset)
        for flight_number, dep_time in flight_pool:
            if thin:
                daily_fare = base_fare + random.randint(-200, 2500)
            else:
                daily_fare = base_fare + random.randint(-300, 800) - (day_offset * 40)

            airline = "IndiGo" if flight_number.startswith("6E") else "Air India"

            observations.append({
                "source": "sample_data",
                "origin": route_origin,
                "destination": route_dest,
                "travel_date": (collection_date + timedelta(days=7)).strftime("%Y-%m-%d"),
                "collection_timestamp": collection_date,
                "advance_days": 7,
                "airline": airline,
                "flight_number": flight_number,
                "departure_time": dep_time,
                "cabin": "economy",
                "total_fare": float(daily_fare),
                "fare_breakdown_available": False,
                "quality_status": "VALID"
            })

    return observations


if __name__ == "__main__":
    dense_route_data = generate_fake_observations("DEL", "BOM", num_days=7, base_fare=4500, thin=False)
    thin_route_data = generate_fake_observations("DEL", "IXL", num_days=7, base_fare=6000, thin=True)

    print(f"Generated {len(dense_route_data)} dense-route observations")
    print(f"Generated {len(thin_route_data)} thin-route observations")
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta

from database.db_setup import SessionLocal
from index_engine.jevons import get_observations_for_date, jevons_movement, daily_stats
from index_engine.credibility import credibility_factor, credibility_weighted_relative, stress_score

app = FastAPI(title="Airfare Price Index API")

# Allow the frontend (served separately, e.g. as a static file or on another port)
# to call this API from the browser without CORS errors
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # fine for MVP demo, restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

ROUTES = [
    {"origin": "DEL", "destination": "BOM", "label": "Dense route"},
    {"origin": "DEL", "destination": "IXL", "label": "Thin route"},
]


@app.get("/")
def root():
    return {"message": "Airfare Price Index API running"}


@app.get("/api/index")
def get_index_all_routes():
    """Returns Jevons movement, credibility-weighted relative, and stress
    score for every tracked route."""
    session = SessionLocal()
    today = datetime.now()
    yesterday = today - timedelta(days=1)
   
    route_results = []

    for r in ROUTES:
        today_obs = get_observations_for_date(session, r["origin"], r["destination"], today)
        yesterday_obs = get_observations_for_date(session, r["origin"], r["destination"], yesterday)

        movement = jevons_movement(today_obs, yesterday_obs)
        stats = daily_stats(today_obs)

        if movement is None:
            route_results.append({
                "route": f"{r['origin']}-{r['destination']}",
                "label": r["label"],
                "status": "no matched observations",
                "median_fare_today": stats["median"],
                "n_observations_today": stats["n"],
            })
            continue

        route_relative = movement["jevons_movement"] / 100
        n_obs = movement["matched_flights"]

        route_results.append({
            "route": f"{r['origin']}-{r['destination']}",
            "label": r["label"],
            "raw_jevons_relative": round(route_relative, 4),
            "raw_percent_change": round((route_relative - 1) * 100, 1),
            "matched_flights": n_obs,
            "median_fare_today": stats["median"],
            "q1_fare_today": stats["q1"],
            "q3_fare_today": stats["q3"],
            "n_observations_today": stats["n"],
        })

    # pooled average across routes with valid movement
    valid_relatives = [r["raw_jevons_relative"] for r in route_results if "raw_jevons_relative" in r]
    pooled_relative = sum(valid_relatives) / len(valid_relatives) if valid_relatives else 1.0

    for r in route_results:
        if "raw_jevons_relative" not in r:
            continue
        cred = credibility_weighted_relative(
            r["raw_jevons_relative"], pooled_relative, r["matched_flights"]
        )
        stress = stress_score(r["raw_jevons_relative"])

        r["credibility_factor"] = round(cred["credibility_factor"], 3)
        r["credibility_weighted_relative"] = round(cred["weighted_relative"], 4)
        r["credibility_weighted_percent_change"] = round((cred["weighted_relative"] - 1) * 100, 1)
        r["stress_score_percent"] = round(stress, 1)

    return {
        "date": today.strftime("%Y-%m-%d"),
        "pooled_class_average_relative": round(pooled_relative, 4),
        "routes": route_results
    }


@app.get("/api/observations/{origin}/{destination}")
def get_raw_observations(origin: str, destination: str):
    """Audit trail — raw observations behind a route's numbers."""
    from database.models import FareObservation
    session = SessionLocal()

    obs = session.query(FareObservation).filter(
        FareObservation.origin == origin.upper(),
        FareObservation.destination == destination.upper(),
        FareObservation.quality_status == "VALID"
    ).order_by(FareObservation.collection_timestamp.desc()).limit(50).all()

    return [
        {
            "flight_number": o.flight_number,
            "airline": o.airline,
            "departure_time": o.departure_time,
            "total_fare": o.total_fare,
            "collection_timestamp": o.collection_timestamp.isoformat(),
            "travel_date": o.travel_date,
            "source": o.source,
        }
        for o in obs
    ]

@app.get("/api/median-history/{origin}/{destination}")
def median_history(origin: str, destination: str, days: int = 7):
    session = SessionLocal()
    history = []
    for i in range(days):
        target_date = datetime.now() - timedelta(days=i)
        obs = get_observations_for_date(session, origin.upper(), destination.upper(), target_date)
        stats = daily_stats(obs)
        history.append({
            "date": target_date.strftime("%Y-%m-%d"),
            "median_fare": stats["median"],
            "n_observations": stats["n"]
        })
    history.reverse()  # oldest to newest, for a left-to-right chart
    return history
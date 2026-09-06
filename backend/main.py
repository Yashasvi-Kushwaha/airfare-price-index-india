import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from datetime import datetime, timedelta

from database.db_setup import SessionLocal
from database.models import FareObservation

from index_engine.jevons import (
    get_observations_for_date,
    jevons_movement,
    daily_stats
)

from index_engine.credibility import (
    credibility_weighted_relative,
    stress_score
)


app = FastAPI(
    title="Airfare Price Index API"
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

ROUTES = [

    {
        "origin": "DEL",
        "destination": "BOM",
        "label": "Dense route"
    },

    {
        "origin": "DEL",
        "destination": "IXL",
        "label": "Thin route"
    },

]


# ---------------------------------------------------------
# DATABASE DEPENDENCY
# ---------------------------------------------------------

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get("/")
def root():

    return {
        "message": "Airfare Price Index API running"
    }


# ---------------------------------------------------------
# DAILY INDEX
# ---------------------------------------------------------

@app.get("/api/index")
def get_index_all_routes(
    session=Depends(get_db)
):

    today = datetime.now()

    yesterday = today - timedelta(days=1)

    route_results = []


    for r in ROUTES:

        today_obs = get_observations_for_date(
            session,
            r["origin"],
            r["destination"],
            today
        )

        yesterday_obs = get_observations_for_date(
            session,
            r["origin"],
            r["destination"],
            yesterday
        )


        movement = jevons_movement(
            today_obs,
            yesterday_obs
        )

        stats = daily_stats(
            today_obs
        )


        if movement is None:

            route_results.append({

                "route":
                    f"{r['origin']}-{r['destination']}",

                "label":
                    r["label"],

                "status":
                    "no matched observations",

                "median_fare_today":
                    stats["median"],

                "n_observations_today":
                    stats["n"],

            })

            continue


        route_relative = (
            movement["jevons_movement"] / 100
        )

        n_obs = movement[
            "matched_flights"
        ]


        route_results.append({

            "route":
                f"{r['origin']}-{r['destination']}",

            "label":
                r["label"],

            "raw_jevons_relative":
                round(route_relative, 4),

            "raw_percent_change":
                round(
                    (route_relative - 1) * 100,
                    1
                ),

            "matched_flights":
                n_obs,

            "median_fare_today":
                stats["median"],

            "q1_fare_today":
                stats["q1"],

            "q3_fare_today":
                stats["q3"],

            "n_observations_today":
                stats["n"],

        })


    # -----------------------------------------------------
    # POOLED RELATIVE
    # -----------------------------------------------------

    valid_relatives = [

        r["raw_jevons_relative"]

        for r in route_results

        if "raw_jevons_relative" in r

    ]


    pooled_relative = (

        sum(valid_relatives)
        / len(valid_relatives)

        if valid_relatives

        else 1.0

    )


    # -----------------------------------------------------
    # CREDIBILITY + STRESS
    # -----------------------------------------------------

    for r in route_results:

        if "raw_jevons_relative" not in r:

            continue


        cred = credibility_weighted_relative(

            r["raw_jevons_relative"],

            pooled_relative,

            r["matched_flights"]

        )


        stress = stress_score(

            r["raw_jevons_relative"]

        )


        r["credibility_factor"] = round(

            cred["credibility_factor"],

            3

        )


        r["credibility_weighted_relative"] = round(

            cred["weighted_relative"],

            4

        )


        r[
            "credibility_weighted_percent_change"
        ] = round(

            (
                cred["weighted_relative"] - 1
            ) * 100,

            1

        )


        r["stress_score_percent"] = round(

            stress,

            1

        )


    return {

        "date":
            today.strftime("%Y-%m-%d"),

        "pooled_class_average_relative":
            round(pooled_relative, 4),

        "routes":
            route_results

    }


# ---------------------------------------------------------
# RAW OBSERVATIONS
# ---------------------------------------------------------

@app.get(
    "/api/observations/{origin}/{destination}"
)
def get_raw_observations(

    origin: str,

    destination: str,

    session=Depends(get_db)

):

    obs = session.query(
        FareObservation
    ).filter(

        FareObservation.origin ==
        origin.upper(),

        FareObservation.destination ==
        destination.upper(),

        FareObservation.quality_status ==
        "VALID"

    ).order_by(

        FareObservation.collection_timestamp.desc()

    ).limit(50).all()


    return [

        {

            "flight_number":
                o.flight_number,

            "airline":
                o.airline,

            "departure_time":
                o.departure_time,

            "total_fare":
                o.total_fare,

            "collection_timestamp":
                o.collection_timestamp.isoformat(),

            "travel_date":
                o.travel_date,

            "advance_days":
                o.advance_days,

            "source":
                o.source,

        }

        for o in obs

    ]


# ---------------------------------------------------------
# MEDIAN HISTORY
# ---------------------------------------------------------

@app.get(
    "/api/median-history/{origin}/{destination}"
)
def median_history(

    origin: str,

    destination: str,

    days: int = 7,

    session=Depends(get_db)

):

    history = []


    for i in range(days):

        target_date = (
            datetime.now()
            - timedelta(days=i)
        )


        obs = get_observations_for_date(

            session,

            origin.upper(),

            destination.upper(),

            target_date

        )


        stats = daily_stats(obs)


        history.append({

            "date":
                target_date.strftime("%Y-%m-%d"),

            "median_fare":
                stats["median"],

            "n_observations":
                stats["n"]

        })


    history.reverse()


    return history


# ---------------------------------------------------------
# LEAD-TIME COMPARISON
# ---------------------------------------------------------

@app.get(
    "/api/lead-time/{origin}/{destination}"
)
def lead_time_comparison(

    origin: str,

    destination: str,

    session=Depends(get_db)

):

    origin = origin.upper()

    destination = destination.upper()


    # -----------------------------------------------------
    # T+7
    # -----------------------------------------------------

    t7_obs = session.query(
        FareObservation
    ).filter(

        FareObservation.origin == origin,

        FareObservation.destination == destination,

        FareObservation.advance_days == 7,

        FareObservation.quality_status == "VALID"

    ).all()


    # -----------------------------------------------------
    # T+30
    # -----------------------------------------------------

    t30_obs = session.query(
        FareObservation
    ).filter(

        FareObservation.origin == origin,

        FareObservation.destination == destination,

        FareObservation.advance_days == 30,

        FareObservation.quality_status == "VALID"

    ).all()


    # -----------------------------------------------------
    # CREATE FLIGHT IDENTITIES
    # -----------------------------------------------------

    def flight_key(o):

        return (

            o.airline,

            o.flight_number,

            o.origin,

            o.destination,

            o.departure_time,

            o.travel_date

        )


    t7_by_flight = {

        flight_key(o): o

        for o in t7_obs

    }


    t30_by_flight = {

        flight_key(o): o

        for o in t30_obs

    }


    # -----------------------------------------------------
    # MATCH SAME FLIGHTS
    # -----------------------------------------------------

    common_keys = (

        set(t7_by_flight.keys())
        &
        set(t30_by_flight.keys())

    )


    matched_flights = []


    for key in common_keys:

        t7_fare = t7_by_flight[
            key
        ].total_fare

        t30_fare = t30_by_flight[
            key
        ].total_fare


        matched_flights.append({

            "airline":
                key[0],

            "flight_number":
                key[1],

            "departure_time":
                key[4],

            "travel_date":
                key[5],

            "T+30_fare":
                t30_fare,

            "T+7_fare":
                t7_fare,

            "percent_change":
                round(

                    (
                        (t7_fare - t30_fare)
                        / t30_fare
                    ) * 100,

                    1

                )

        })


    # -----------------------------------------------------
    # MEDIANS
    # -----------------------------------------------------

    t7_stats = daily_stats(
        t7_obs
    )

    t30_stats = daily_stats(
        t30_obs
    )


    # -----------------------------------------------------
    # MEDIAN PERCENT CHANGE
    # -----------------------------------------------------

    percent_increase = None


    if (

        t30_stats["median"] is not None

        and

        t7_stats["median"] is not None

        and

        t30_stats["median"] != 0

    ):

        percent_increase = round(

            (
                (
                    t7_stats["median"]
                    -
                    t30_stats["median"]
                )

                /

                t30_stats["median"]

            ) * 100,

            1

        )


    # -----------------------------------------------------
    # RETURN
    # -----------------------------------------------------

    return {

        "route":
            f"{origin}-{destination}",

        "T+30_median_fare":
            t30_stats["median"],

        "T+7_median_fare":
            t7_stats["median"],

        "percent_increase_last_minute":
            percent_increase,

        "T+30_observations":
            t30_stats["n"],

        "T+7_observations":
            t7_stats["n"],

        "matched_flights":
            len(matched_flights),

        "flight_comparison":
            sorted(

                matched_flights,

                key=lambda x:
                    x["flight_number"]

            )

    }
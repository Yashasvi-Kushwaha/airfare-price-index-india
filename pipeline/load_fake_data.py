import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from datetime import datetime, timedelta

from database.db_setup import SessionLocal
from database.models import FareObservation

from pipeline.fake_data_generator import (
    generate_lead_time_observations,
    generate_daily_history
)


session = SessionLocal()


try:

    # ---------------------------------------------------------
    # 1. CLEAR OLD SAMPLE DATA
    # ---------------------------------------------------------

    session.query(FareObservation).filter(
        FareObservation.source == "sample_data"
    ).delete()

    session.commit()

    print("Cleared old sample data.")


    # ---------------------------------------------------------
    # 2. FIXED TRAVEL DATES
    # ---------------------------------------------------------

    # DEL-BOM travel date
    bom_travel_date = (
        datetime.now() + timedelta(days=30)
    ).strftime("%Y-%m-%d")

    # DEL-IXL travel date
    ixl_travel_date = (
        datetime.now() + timedelta(days=30)
    ).strftime("%Y-%m-%d")


    # ---------------------------------------------------------
    # 3. LEAD-TIME DATA
    # ---------------------------------------------------------

    print("\nGenerating T+30 and T+7 data...")


    # Dense route
    dense_lead_time = generate_lead_time_observations(
        route_origin="DEL",
        route_dest="BOM",
        travel_date=bom_travel_date,
        base_fare=4500,
        thin=False
    )


    # Thin route
    thin_lead_time = generate_lead_time_observations(
        route_origin="DEL",
        route_dest="IXL",
        travel_date=ixl_travel_date,
        base_fare=6000,
        thin=True
    )


    # ---------------------------------------------------------
    # 4. DAILY HISTORY
    # ---------------------------------------------------------

    print("Generating daily history...")


    dense_history = generate_daily_history(
        route_origin="DEL",
        route_dest="BOM",
        num_days=7,
        base_fare=5000,
        thin=False,
        advance_days=7
    )


    thin_history = generate_daily_history(
        route_origin="DEL",
        route_dest="IXL",
        num_days=7,
        base_fare=6800,
        thin=True,
        advance_days=7
    )


    # ---------------------------------------------------------
    # 5. COMBINE DATA
    # ---------------------------------------------------------

    all_data = (
        dense_lead_time
        + thin_lead_time
        + dense_history
        + thin_history
    )


    # ---------------------------------------------------------
    # 6. INSERT INTO DATABASE
    # ---------------------------------------------------------

    for obs_dict in all_data:

        obs = FareObservation(**obs_dict)

        session.add(obs)


    session.commit()


    # ---------------------------------------------------------
    # 7. SUMMARY
    # ---------------------------------------------------------

    print(
        f"\nInserted {len(all_data)} sample observations."
    )

    print("\nLead-time data:")

    print(
        f"DEL-BOM: "
        f"{len(dense_lead_time)} observations"
    )

    print(
        f"DEL-IXL: "
        f"{len(thin_lead_time)} observations"
    )

    print("\nHistory data:")

    print(
        f"DEL-BOM: "
        f"{len(dense_history)} observations"
    )

    print(
        f"DEL-IXL: "
        f"{len(thin_history)} observations"
    )

    print("\nTravel dates:")

    print(f"DEL-BOM → {bom_travel_date}")
    print(f"DEL-IXL → {ixl_travel_date}")

    print("\nDatabase population complete.")


except Exception as e:

    session.rollback()

    print(f"\nERROR: {e}")

    raise


finally:

    session.close()
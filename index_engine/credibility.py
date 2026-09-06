import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from database.db_setup import SessionLocal
from index_engine.jevons import get_observations_for_date, jevons_movement


def credibility_factor(n_observations, k=3):
    """
    Bühlmann-style credibility factor.
    Z approaches 1 as observations grow (trust the route's own data more).
    Z approaches 0 with few observations (lean on the pooled/class average).
    k is a tunable constant — NOT rigorously fitted for this MVP, stated
    honestly as an illustrative/experimental value.
    """
    return n_observations / (n_observations + k)


def credibility_weighted_relative(route_relative, pooled_relative, n_observations, k=3):
    """
    Blends a route's own Jevons relative with a pooled class-average relative,
    weighted by how much data backs the route's own estimate.
    """
    Z = credibility_factor(n_observations, k)
    weighted = Z * route_relative + (1 - Z) * pooled_relative
    return {
        "credibility_factor": Z,
        "weighted_relative": weighted,
        "raw_relative": route_relative,
        "pooled_relative": pooled_relative,
        "n_observations": n_observations
    }


def stress_score(route_relative, baseline_relative=1.0):
    """
    Unweighted, raw deviation — computed independently of credibility.
    This is what surfaces route-level stress that credibility weighting
    would otherwise dampen in the aggregate index.
    Returns percentage deviation from baseline (1.0 = no change).
    """
    return (route_relative - baseline_relative) * 100


if __name__ == "__main__":
    session = SessionLocal()
    today = datetime.now()
    yesterday = today - timedelta(days=1)

    routes = [
        {"origin": "DEL", "destination": "BOM", "label": "Dense route"},
        {"origin": "DEL", "destination": "IXL", "label": "Thin route"},
    ]

    route_results = []

    for r in routes:
        today_obs = get_observations_for_date(session, r["origin"], r["destination"], today)
        yesterday_obs = get_observations_for_date(session, r["origin"], r["destination"], yesterday)

        movement = jevons_movement(today_obs, yesterday_obs)

        if movement is None:
            print(f"{r['label']} ({r['origin']}-{r['destination']}): no matched flights, skipping")
            continue

        route_relative = movement["jevons_movement"] / 100
        n_obs = movement["matched_flights"]

        route_results.append({
            "label": r["label"],
            "route": f"{r['origin']}-{r['destination']}",
            "raw_relative": route_relative,
            "n_observations": n_obs
        })

    print(f"\nDEBUG - route_results: {route_results}\n")

    if route_results:
        pooled_relative = sum(r["raw_relative"] for r in route_results) / len(route_results)
    else:
        pooled_relative = 1.0

    print(f"Pooled/class average relative: {pooled_relative:.4f}\n")

    for r in route_results:
        cred = credibility_weighted_relative(
            r["raw_relative"], pooled_relative, r["n_observations"]
        )
        stress = stress_score(r["raw_relative"])

        print(f"--- {r['label']} ({r['route']}) ---")
        print(f"  Observations matched:        {r['n_observations']}")
        print(f"  Raw Jevons relative:          {r['raw_relative']:.4f}  ({(r['raw_relative']-1)*100:+.1f}%)")
        print(f"  Credibility factor (Z):       {cred['credibility_factor']:.3f}")
        print(f"  Credibility-weighted relative:{cred['weighted_relative']:.4f}  ({(cred['weighted_relative']-1)*100:+.1f}%)")
        print(f"  Stress score (raw deviation): {stress:+.1f}%")
        print()
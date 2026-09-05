import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_setup import SessionLocal
from database.models import FareObservation
from pipeline.fake_data_generator import generate_fake_observations

session = SessionLocal()

# Clear old sample data first, so reruns don't duplicate/stack
session.query(FareObservation).filter(FareObservation.source == "sample_data").delete()
session.commit()
print("Cleared old sample data.")

dense_route_data = generate_fake_observations("DEL", "BOM", num_days=7, base_fare=4500, thin=False)
thin_route_data = generate_fake_observations("DEL", "IXL", num_days=7, base_fare=6000, thin=True)
# adjust "IXL" to your real chosen thin route code

all_data = dense_route_data + thin_route_data

for obs_dict in all_data:
    obs = FareObservation(**obs_dict)
    session.add(obs)

session.commit()
print(f"Inserted {len(all_data)} sample observations into database.")
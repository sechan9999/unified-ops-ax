"""Fleet Telemetry Data Generator for Unified Ops AX."""
from datetime import datetime
import numpy as np
import pandas as pd


def generate_fleet_data(num_units: int = 18) -> pd.DataFrame:
    """Generates mock real-time telemetry dataframe for autonomous fleet units."""
    np.random.seed(42)
    unit_ids = [f"AX-{1000 + i}" for i in range(num_units)]
    types = ["Autonomous Van", "Heavy Hauler", "Scout Drone", "Rapid Courier"]
    statuses = ["Active", "Active", "Active", "Warning", "Critical", "Idle"]

    # Hub location: San Francisco / Bay Area center
    base_lat, base_lon = 37.7749, -122.4194
    fleet = []

    for uid in unit_ids:
        status = np.random.choice(statuses, p=[0.55, 0.15, 0.1, 0.1, 0.05, 0.05])
        lat = base_lat + np.random.normal(0, 0.04)
        lon = base_lon + np.random.normal(0, 0.06)
        battery = np.random.randint(15, 100) if status != "Critical" else np.random.randint(5, 18)
        speed = np.random.randint(20, 65) if status in ["Active", "Warning"] else 0

        fleet.append({
            "Unit ID": uid,
            "Type": np.random.choice(types),
            "Status": status,
            "Battery (%)": battery,
            "Speed (mph)": speed,
            "Latitude": lat,
            "Longitude": lon,
            "Heading": np.random.randint(0, 360),
            "Signal Strength": f"{np.random.randint(85, 99)} dBm",
            "ETA (mins)": np.random.randint(5, 45) if status == "Active" else 0,
            "Last Telemetry Ping": datetime.utcnow().strftime("%H:%M:%S UTC")
        })

    return pd.DataFrame(fleet)

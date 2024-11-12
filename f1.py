import fastf1 as ff1
import pandas as pd
import os

# Ensure cache directory exists
cache_dir = 'telemetry_cache'
os.makedirs(cache_dir, exist_ok=True)  # Automatically creates the directory if it doesn't exist

ff1.Cache.enable_cache(cache_dir)  # Enable caching

def save_telemetry_to_csv(session_type, year, gp_name, session_name):
    """
    Collect telemetry data from F1 session and save it to a CSV file.
    """
    session = ff1.get_session(year, gp_name, session_type)
    session.load()  # Loads telemetry data

    telemetry_data = []
    for lap in session.laps.iterlaps():
        lap_data = lap[1].get_car_data().add_distance()  # Get telemetry per lap
        telemetry_data.append(lap_data)

    # Concatenate all laps into one DataFrame
    full_telemetry = pd.concat(telemetry_data, ignore_index=True)
    
    # Save data as CSV
    file_path = f"{session_name}.csv"
    full_telemetry.to_csv(file_path, index=False)
    print(f"Telemetry data saved to {file_path}")

# Example usage
save_telemetry_to_csv('Q', 2023, 'Monaco', 'Monaco_Qualifying')

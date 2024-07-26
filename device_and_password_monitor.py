import random
import string
import requests
import platform
import psutil
import os

DEVICE_NAME = platform.node()

# List of known game executables
KNOWN_GAMES = {
    'csgo.exe': 'Counter-Strike: Global Offensive',
    'dota2.exe': 'Dota 2',
    'valorant.exe': 'Valorant',
    'leagueoflegends.exe': 'League of Legends',
    # Add more games here
}


def generate_password():
    return "".join(random.choices(string.digits, k=4))


def update_password(device_name):
    new_password = generate_password()
    response = requests.post(
        "http://localhost:5000/reserve",
        json={
            "username": "system",
            "email": "system@lanroom.com",
            "device": device_name,
        },
    )
    if response.status_code == 200:
        print(f"Password for {device_name} updated to {new_password}")
    else:
        print("Failed to update password")


def get_running_games():
    running_games = []
    for process in psutil.process_iter(['pid', 'name']):
        try:
            if process.info['name'].lower() in KNOWN_GAMES:
                running_games.append(KNOWN_GAMES[process.info['name'].lower()])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return running_games


def update_device_status(device_name):
    # Check if the device is off (simulate by checking if no games are running)
    running_games = get_running_games()
    if not running_games:
        status = "Available"
    else:
        status = "In Use"
    
    response = requests.post(
        "http://localhost:5000/update_status",
        json={
            "device": device_name,
            "status": status,
        },
    )
    if response.status_code == 200:
        print(f"Status for {device_name} updated to {status}")
    else:
        print("Failed to update status")


if __name__ == "__main__":
    update_password(DEVICE_NAME)
    update_device_status(DEVICE_NAME)

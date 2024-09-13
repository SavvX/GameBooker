import random
import string
import requests
import platform
import psutil
import time
import threading
import win32event
import win32security
from win32com import adsi

DEVICE_NAME = 'PC2'

# List of known game executables
KNOWN_GAMES = {
    'csgo.exe': 'Counter-Strike: Global Offensive',
    'dota2.exe': 'Dota 2',
    'valorant.exe': 'Valorant',
    'leagueoflegends.exe': 'League of Legends',
    # Add more games here
}

def generate_pin():
    return "".join(random.choices(string.digits, k=4))

def update_pin(device_name):
    new_pin = generate_pin()
    response = requests.post(
        "http://192.168.1.57:5000/reserve",
        json={
            "username": "system",
            "email": "system@lanroom.com",
            "device": device_name,
            "pin": new_pin,  # Sending new pin in the reservation request
        },
    )
    if response.status_code == 200:
        print(f"PIN for {device_name} updated to {new_pin}")
    else:
        print("Failed to update PIN")

def set_password(username, password):
    ads_obj = adsi.ADsGetObject(f"WinNT://localhost/{username},user")
    ads_obj.SetPassword(password)

def verify_success(username, password):
    from win32security import LogonUser
    from win32con import LOGON32_LOGON_INTERACTIVE, LOGON32_PROVIDER_DEFAULT
    try:
        LogonUser(username, None, password, LOGON32_LOGON_INTERACTIVE, LOGON32_PROVIDER_DEFAULT)
    except:
        return False
    return True

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
    running_games = get_running_games()
    if not running_games:
        status = "Available"
    else:
        status = "In Use"

    response = requests.post(
        "http://192.168.1.57:5000/update_status",
        json={
            "device": device_name,
            "status": status,
        },
    )
    if response.status_code == 200:
        print(f"Status for {device_name} updated to {status}")
    else:
        print("Failed to update status")

def check_lock_state():
    # Create an event handle
    event_handle = win32event.CreateEvent(None, False, False, None)

    # Monitor system events
    while True:
        # Wait for an event
        result = win32event.WaitForSingleObject(event_handle, win32event.INFINITE)

        if result == win32event.WAIT_OBJECT_0:
            print("Detected system lock/unlock event")
            update_pin(DEVICE_NAME)
            update_device_status(DEVICE_NAME)
            print("Password changed and device status updated")

def monitor_locks_and_passwords():
    # Start a background thread to monitor the lock/unlock events
    threading.Thread(target=check_lock_state, daemon=True).start()

if __name__ == "__main__":
    print("Script is running...")
    monitor_locks_and_passwords()

    # Main thread can perform other tasks if needed
    try:
        while True:
            time.sleep(60)  # Sleep and keep the script running
    except KeyboardInterrupt:
        print("Script terminated.")
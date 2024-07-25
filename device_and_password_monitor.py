import random
import string
import requests
import platform
import socket
import time

# Server URLs
SERVER_URL_RESERVE = "http://localhost:5000/reserve"
SERVER_URL_STATUS = "http://localhost:5000/status"
SERVER_URL_OFFLINE = "http://localhost:5000/device_offline"

# Device Information
DEVICE_NAME = platform.node()  # Get the name of the device (e.g., PC1, PC2)


def generate_password():
    """Generate a random 4-digit password."""
    return "".join(random.choices(string.digits, k=4))


def update_password(device_name):
    """Update the password for the device."""
    new_password = generate_password()
    response = requests.post(
        SERVER_URL_RESERVE,
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


def is_device_online():
    """Check if the device is online."""
    try:
        # Try connecting to a known address to check internet connectivity
        socket.create_connection(("8.8.8.8", 80), timeout=5)
        return True
    except OSError:
        return False


def notify_device_offline():
    """Notify the server that the device is offline."""
    response = requests.post(SERVER_URL_OFFLINE, json={"device": DEVICE_NAME})
    print(f"Device offline notification: {response.json()}")


def fetch_device_status():
    """Fetch the device status from the server."""
    response = requests.get(SERVER_URL_STATUS)
    if response.status_code == 200:
        status = response.json()
        if DEVICE_NAME in status and status[DEVICE_NAME] == "Available":
            print(f"{DEVICE_NAME} is available.")
        else:
            print(f"{DEVICE_NAME} status: {status.get(DEVICE_NAME, 'Unknown')}")
    else:
        print("Failed to fetch device status")


def main():
    """Main function to run the device monitoring and password updating."""
    while True:
        if not is_device_online():
            notify_device_offline()
        else:
            fetch_device_status()
            update_password(DEVICE_NAME)
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    main()

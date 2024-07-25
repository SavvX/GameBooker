import random
import string
import requests
import platform

DEVICE_NAME = platform.node()

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


if __name__ == "__main__":
    update_password(DEVICE_NAME)

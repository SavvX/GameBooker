from pynput import mouse, keyboard
import csv
from datetime import datetime

# Create or open a CSV file
with open('input_log.csv', 'a', newline='') as file:
    writer = csv.writer(file)

    def log_and_print(event_type, *args):
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Format time to include milliseconds
        message = f"{timestamp} - {event_type}: {' '.join(map(str, args))}"
        print(message)
        writer.writerow([timestamp, event_type] + list(args))

    def on_press(key):
        try:
            log_and_print('Key Press', key.char)
        except AttributeError:
            log_and_print('Key Press', str(key))
        if key == keyboard.Key.esc:  # Stop when the 'esc' key is pressed
            return False  # This will stop the listener

    def on_click(x, y, button, pressed):
        if pressed:
            log_and_print('Mouse Click', button, x, y)

    # Set up listeners
    with mouse.Listener(on_click=on_click) as mouse_listener, keyboard.Listener(on_press=on_press) as keyboard_listener:
        keyboard_listener.join()  # This will block until the 'esc' key is presseddsadsa

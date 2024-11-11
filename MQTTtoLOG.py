import paho.mqtt.client as mqtt
import csv
import os
import time

# Initialize variables for data
data = {
    "tidGaaet": None,
    "P_ude": None,
    "P_inde": None,
    "RH": None,
    "SCD30_temp": None,
    "htu_temp": None,
    "T_ude": None,
    "CO2": None,
    "O2": None,
    "CH4": None,
    "MIPEX": None,
    "EC": None,
    "Perc_bat": None,
    "P_diff": None
}

# USB path where CSV will be saved
usb_path = '/media/usb/data_log.csv'

# Callback when a message is received
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()

    # Check which topic has been updated and update the corresponding value
    if topic == "topic/tidGaaet":
        data["tidGaaet"] = payload
    elif topic == "topic/P_ude":
        data["P_ude"] = payload
    elif topic == "topic/P_inde":
        data["P_inde"] = payload
    elif topic == "topic/RH":
        data["RH"] = payload
    elif topic == "topic/SCD30_temp":
        data["SCD30_temp"] = payload
    elif topic == "topic/htu_temp":
        data["htu_temp"] = payload
    elif topic == "topic/T_ude":
        data["T_ude"] = payload
    elif topic == "topic/CO2":
        data["CO2"] = payload
    elif topic == "topic/O2":
        data["O2"] = payload
    elif topic == "topic/CH4":
        data["CH4"] = payload
    elif topic == "topic/MIPEX":
        data["MIPEX"] = payload
    elif topic == "topic/EC":
        data["EC"] = payload
    elif topic == "topic/Perc_bat":
        data["Perc_bat"] = payload
    elif topic == "topic/P_diff":
        data["P_diff"] = payload

    # If "topic/tidGaaet" is updated, save the data to CSV
    if topic == "topic/tidGaaet":
        save_to_csv(data)
        reset_data()

# Save data to CSV
def save_to_csv(data):
    # Ensure the USB drive exists and is writable
    if not os.path.exists(usb_path):
        print(f"USB drive not found at {usb_path}. Exiting.")
        return

    # Open the CSV file and append new row
    with open(usb_path, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())

        # Write headers if file is empty
        if file.tell() == 0:
            writer.writeheader()

        # Write the data as a row
        writer.writerow(data)
        print(f"Data saved: {data}")

# Reset the data dictionary to 'null'
def reset_data():
    global data
    for key in data:
        data[key] = None

# Setup MQTT client
client = mqtt.Client()

# Set up MQTT callbacks
client.on_message = on_message

# Connect to the MQTT broker (assumes broker is on the same Raspberry Pi)
client.connect("127.0.0.1", keepalive=60)

# Subscribe to topics
topics = [
    "topic/tidGaaet",
    "topic/P_ude",
    "topic/P_inde",
    "topic/RH",
    "topic/SCD30_temp",
    "topic/htu_temp",
    "topic/T_ude",
    "topic/CO2",
    "topic/O2",
    "topic/CH4",
    "topic/MIPEX",
    "topic/EC",
    "topic/Perc_bat",
    "topic/P_diff"
]

for topic in topics:
    client.subscribe(topic)

# Loop to keep the script running and listening for MQTT messages
client.loop_start()

try:
    # Keep the script running
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Script interrupted, exiting...")
finally:
    client.loop_stop()

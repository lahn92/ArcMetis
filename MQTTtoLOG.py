#
#Logs the data recived from MQTT to a file on a USB drive attached to raspberry pi (drive name must be ARCMETIS)
#
import csv
import os
import time
from datetime import datetime
import paho.mqtt.client as mqtt

# Initialize variables for data and logging status
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

latitude = None
longitude = None
logging_enabled = False
csv_file_path = None

# USB base path and specific path for data logging
usb_base_path = '/media/arcmetis/ARCMETIS/'
usb_present = os.path.exists(usb_base_path)

# MQTT topics for USB status and GPS coordinates
usb_status_topic = "status/noUSB"
gps_latitude_topic = "platform/gps_latitude"
gps_longitude_topic = "platform/gps_longitude"

# Callback when a message is received
def on_message(client, userdata, msg):
    global logging_enabled, csv_file_path, latitude, longitude
    topic = msg.topic
    payload = msg.payload.decode()

    # Debug: print received topic and payload
    print(f"Received message: Topic = {topic}, Payload = {payload}")

    # Handle GPS coordinates
    if topic == gps_latitude_topic:
        latitude = payload
    elif topic == gps_longitude_topic:
        longitude = payload

    # Start or stop logging based on "status/logging"
    elif topic == "status/logging":
        if payload in ["1", "1.0"] and not logging_enabled and usb_present:
            logging_enabled = True
            # Create a new CSV file with UTC date and time in the name
            current_time = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
            csv_file_path = os.path.join(usb_base_path, f"data_log_{current_time}.csv")
            write_info_block()
            print(f"Logging started. Data will be saved to {csv_file_path}")
        elif payload in ["0", "0.0"] and logging_enabled:
            logging_enabled = False
            print("Logging stopped.")

    # Update data dictionary when probe topics are received
    elif logging_enabled and topic.startswith("probe/"):
        key = topic.split('/')[-1]
        if key in data:
            data[key] = payload

        # Save to CSV when "tidGaaet" topic is updated
        if topic == "probe/tidGaaet":
            save_to_csv(data)
            reset_data()

# Write the information block to the CSV file
def write_info_block():
    if csv_file_path is None:
        print("CSV file path is not set.")
        return

    # Write the information block
    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow(["Info Block"])
        writer.writerow(["Time", current_time])
        writer.writerow(["Data", "Logging started"])
        writer.writerow(["Latitude", latitude if latitude else "Unknown"])
        writer.writerow(["Longitude", longitude if longitude else "Unknown"])
        writer.writerow([])  # Add a blank line for separation
        print("Information block written to CSV.")

# Save data to CSV
def save_to_csv(data):
    if csv_file_path is None:
        print("CSV file path is not set.")
        return

    # Append new row to the CSV file
    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data.keys())

        # Write headers if file is empty
        if file.tell() == 0:
            writer.writeheader()

        # Write the data as a row
        writer.writerow(data)
        print(f"Data saved: {data}")

# Reset the data dictionary to 'None'
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

# USB fault handler: check for USB presence and publish status if absent
if not usb_present:
    client.publish(usb_status_topic, "1")
    print(f"USB drive not found at {usb_base_path}. 'status/noUSB' set to 1.")
else:
    client.publish(usb_status_topic, "0")
    print("USB drive is present.")

# Subscribe to topics
topics = [
    "probe/tidGaaet",
    "probe/P_ude",
    "probe/P_inde",
    "probe/RH",
    "probe/SCD30_temp",
    "probe/htu_temp",
    "probe/T_ude",
    "probe/CO2",
    "probe/O2",
    "probe/CH4",
    "probe/MIPEX",
    "probe/EC",
    "probe/Perc_bat",
    "probe/P_diff",
    "status/logging",
    "gps_latitude_topic",
    "gps_longitude_topic"
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

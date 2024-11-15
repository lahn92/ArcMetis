import glob
from pymavlink import mavutil
import paho.mqtt.client as mqtt
import time
import os

# Configuration
baud_rate = 57600
mqtt_broker = '127.0.0.1'  # Replace with your MQTT broker's IP
button_channel = 8  # RC8 corresponds to channel 8
button_threshold = 1500  # Threshold for button press
mqtt_topic = "status/init_sampling"  # Topic to publish to
mav_error_topic = "status/mavError"  # Topic to publish MAVLink connection error status

# Find the correct device by searching for available ttyACM* devices
def find_mavlink_device():
    possible_devices = glob.glob('/dev/ttyACM*')
    for device in possible_devices:
        try:
            master = mavutil.mavlink_connection(device, baud=baud_rate)
            print(f"Checking {device} for heartbeat...")
            master.wait_heartbeat(timeout=5)
            print(f"Connected to MAVLink device at {device}")
            return master
        except Exception as e:
            print(f"Device {device} is not a MAVLink device: {e}")
    print("No valid MAVLink device found.")
    return None

# Attempt to locate and connect to the MAVLink device
master = find_mavlink_device()

# Create a connection to the MQTT broker
client = mqtt.Client()
client.connect(mqtt_broker)

# Function to monitor MAVLink connection and publish status
def monitor_mavlink_connection():
    global master
    try:
        # Check if heartbeat can be received
        master.wait_heartbeat(timeout=5)
        client.publish(mav_error_topic, "0")  # Connection is OK
    except Exception as e:
        print(f"MAVLink connection lost: {e}")
        client.publish(mav_error_topic, "1")  # Connection lost
        master = find_mavlink_device()  # Attempt to reconnect

# Function to monitor button presses and publish MQTT messages
def monitor_button_press():
    global previous_state
    try:
        rc_channels = master.recv_match(type='RC_CHANNELS', blocking=True)
        if rc_channels:
            button_value = getattr(rc_channels, f'chan{button_channel}_raw', 0)
            current_state = 1 if button_value > button_threshold else 0
            if current_state != previous_state:  # Only publish if the state changes
                print(f"Button state changed to {current_state}. Publishing to {mqtt_topic}...")
                client.publish(mqtt_topic, str(current_state))
                previous_state = current_state
    except Exception as e:
        print(f"Error monitoring button press: {e}")

# Telemetry publishing functions
def publish_mode(client):
    mode = master.flightmode
    print(f"Current mode: {mode}")
    client.publish("platform/mode", mode)

def publish_battery_voltage(client):
    battery = master.recv_match(type='BATTERY_STATUS', blocking=True)
    if battery and battery.voltages:
        valid_voltages = [v for v in battery.voltages if v != 65535]
        if valid_voltages:
            voltage = valid_voltages[0] / 1000.0
            print(f"Battery voltage: {voltage:.2f}V")
            client.publish("platform/battery_voltage", voltage)

def publish_gps_coordinates(client):
    gps = master.recv_match(type='GPS_RAW_INT', blocking=True)
    if gps:
        latitude = gps.lat / 1e7
        longitude = gps.lon / 1e7
        altitude = gps.alt / 1e3
        print(f"GPS: Lat={latitude}, Lon={longitude}, Alt={altitude}m")
        client.publish("platform/gps_latitude", latitude)
        client.publish("platform/gps_longitude", longitude)
        client.publish("platform/gps_altitude", altitude)

def publish_arming_status(client):
    heartbeat = master.recv_match(type='HEARTBEAT', blocking=True)
    if heartbeat:
        armed = heartbeat.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
        arming_status = "armed" if armed else "disarmed"
        print(f"Arming status: {arming_status}")
        client.publish("platform/arming_status", arming_status)

def publish_gps_speed(client):
    gps = master.recv_match(type='GPS_RAW_INT', blocking=True)
    if gps:
        gps_speed = gps.vel / 100.0
        print(f"GPS speed: {gps_speed} m/s")
        client.publish("platform/gps_speed", gps_speed)

def publish_heading(client):
    vfr_hud = master.recv_match(type='VFR_HUD', blocking=True)
    if vfr_hud:
        heading = vfr_hud.heading
        print(f"Heading: {heading}°")
        client.publish("platform/heading", heading)

# Dictionary of telemetry functions
telemetry_functions = {
    "mode": publish_mode,
    "battery_voltage": publish_battery_voltage,
    "gps_coordinates": publish_gps_coordinates,
    "arming_status": publish_arming_status,
    "gps_speed": publish_gps_speed,
    "heading": publish_heading,
}

# Main loop
try:
    previous_state = None  # Track the previous button state
    while True:
        # Monitor MAVLink connection
        monitor_mavlink_connection()

        # Monitor button presses
        if master:
            monitor_button_press()

        # Publish telemetry
        for name, func in telemetry_functions.items():
            print(f"Publishing {name}...")
            func(client)

        # Sleep to limit execution frequency
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Exiting...")

finally:
    if master:
        master.close()
    client.disconnect()

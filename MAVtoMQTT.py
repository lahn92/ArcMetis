import glob
from pymavlink import mavutil
import paho.mqtt.client as mqtt
import time
import os

# Configuration
baud_rate = 57600
mqtt_broker = '127.0.0.1'  # Replace with your MQTT broker's IP

# Find the correct device by searching for available ttyACM* devices
def find_mavlink_device():
    possible_devices = glob.glob('/dev/ttyACM*')
    for device in possible_devices:
        try:
            # Try to create a MAVLink connection to test the device
            master = mavutil.mavlink_connection(device, baud=baud_rate)
            # Wait briefly for a heartbeat to confirm it's a MAVLink device
            print(f"Checking {device} for heartbeat...")
            master.wait_heartbeat(timeout=5)  # Timeout after 5 seconds if no heartbeat
            print(f"Connected to MAVLink device at {device}")
            return master  # Return the valid MAVLink connection
        except Exception as e:
            print(f"Device {device} is not a MAVLink device: {e}")
    print("No valid MAVLink device found.")
    return None

# Attempt to locate and connect to the MAVLink device
master = find_mavlink_device()
if not master:
    raise SystemExit("MAVLink device not found. Exiting...")

# Create a connection to the MQTT broker
client = mqtt.Client()
client.connect(mqtt_broker)

# Function to set system time based on GPS
def set_system_time():
    system_time = master.recv_match(type='SYSTEM_TIME', blocking=True)
    if system_time and system_time.time_unix_usec > 0:
        utc_time = system_time.time_unix_usec / 1e6  # Convert microseconds to seconds
        utc_time_struct = time.gmtime(utc_time)
        formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', utc_time_struct)
        print(f"Setting system time to: {formatted_time}")
        os.system(f"sudo date -s '{formatted_time}'")
    else:
        print("No valid GPS time available.")

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
            voltage = valid_voltages[0] / 1000.0  # Convert millivolts to volts
            print(f"Battery voltage: {voltage:.2f}V")
            client.publish("platform/battery_voltage", voltage)
        else:
            print("No valid battery voltage readings.")
    else:
        print("Battery status not available or invalid data.")

def publish_gps_coordinates(client):
    gps = master.recv_match(type='GPS_RAW_INT', blocking=True)
    if gps:
        latitude = gps.lat / 1e7  # Convert from integer format to degrees
        longitude = gps.lon / 1e7
        altitude = gps.alt / 1e3  # Convert from millimeters to meters
        print(f"GPS coordinates: Lat={latitude}, Lon={longitude}, Alt={altitude}m")
        client.publish("platform/gps_latitude", latitude)
        client.publish("platform/gps_longitude", longitude)
        client.publish("platform/gps_altitude", altitude)
    else:
        print("GPS data not available.")

# Additional telemetry publishing functions

def publish_arming_status(client):
    # The arming status is available in the HEARTBEAT message
    heartbeat = master.recv_match(type='HEARTBEAT', blocking=True)
    if heartbeat:
        armed = heartbeat.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
        arming_status = "armed" if armed else "disarmed"
        print(f"Arming status: {arming_status}")
        client.publish("platform/arming_status", arming_status)
    else:
        print("Arming status not available.")

def publish_system_status(client):
    # System status available in the HEARTBEAT message
    heartbeat = master.recv_match(type='HEARTBEAT', blocking=True)
    if heartbeat:
        system_status = heartbeat.system_status
        print(f"System status: {system_status}")
        client.publish("platform/system_status", system_status)
    else:
        print("System status not available.")

def publish_gps_speed(client):
    # GPS speed available in the GPS_RAW_INT message
    gps = master.recv_match(type='GPS_RAW_INT', blocking=True)
    if gps:
        gps_speed = gps.vel / 100.0  # Convert from cm/s to m/s
        print(f"GPS speed: {gps_speed} m/s")
        client.publish("platform/gps_speed", gps_speed)
    else:
        print("GPS speed not available.")

def publish_battery_current(client):
    # Battery current available in the BATTERY_STATUS message
    battery = master.recv_match(type='BATTERY_STATUS', blocking=True)
    if battery:
        current = battery.current_battery / 100.0  # Convert from centiamps to amps
        print(f"Battery current: {current} A")
        client.publish("platform/battery_current", current)
    else:
        print("Battery current not available.")

def publish_heading(client):
    # Heading may also be available in the VFR_HUD message
    vfr_hud = master.recv_match(type='VFR_HUD', blocking=True)
    if vfr_hud:
        heading = vfr_hud.heading  # Heading directly in degrees
        print(f"Heading: {heading}°")
        client.publish("platform/heading", heading)
    else:
        print("Heading data not available.")



# Dictionary of telemetry functions for easy addition
telemetry_functions = {
    "mode": publish_mode,
    "battery_voltage": publish_battery_voltage,
    "gps_coordinates": publish_gps_coordinates,
    "arming_status": publish_arming_status,
    "system_status": publish_system_status,
    "gps_speed": publish_gps_speed,
    "battery_current": publish_battery_current,
    "heading": publish_heading
    # Add additional telemetry functions here
}


# Main loop to periodically set system time and publish telemetry data
try:
    while True:
        # Set system time from GPS
        set_system_time()

        # Publish all telemetry items
        for name, func in telemetry_functions.items():
            print(f"Publishing {name}...")
            func(client)

        time.sleep(5)  # Adjust the frequency of data collection as needed

except KeyboardInterrupt:
    print("Exiting...")

finally:
    # Close the MAVLink connection and MQTT client
    if master:
        master.close()
    client.disconnect()

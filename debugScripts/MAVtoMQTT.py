from pymavlink import mavutil
import paho.mqtt.client as mqtt
import time
import os

# Configuration
connection_string = '/dev/ttyACM0'
baud_rate = 57600
mqtt_broker = '192.168.1.64'  # Replace with your MQTT broker's IP

# Create a connection to the vehicle
master = mavutil.mavlink_connection(connection_string, baud=baud_rate)

# Wait for the first heartbeat
print("Waiting for heartbeat...")
master.wait_heartbeat()
print("Heartbeat from vehicle (system_id: {}, component_id: {})".format(master.target_system, master.target_component))

def set_system_time():
    # Get the current UTC time from the GPS
    system_time = master.recv_match(type='SYSTEM_TIME', blocking=True)
    if system_time and system_time.time_unix_usec > 0:
        utc_time = system_time.time_unix_usec / 1e6  # Convert microseconds to seconds
        # Convert UTC time to a formatted string
        utc_time_struct = time.gmtime(utc_time)  # Convert to struct_time for formatting
        
        # Format the time in a way suitable for the `date` command
        formatted_time = time.strftime('%Y-%m-%d %H:%M:%S', utc_time_struct)
        print(f"Setting system time to: {formatted_time}")

        # Use the `date` command to set the system time
        os.system(f"sudo date -s '{formatted_time}'")
    else:
        print("No valid GPS time available.")

def publish_telemetry(client):
    # Get vehicle mode
    mode = master.flightmode
    print("Current mode: {}".format(mode))
    client.publish("vehicle/mode", mode)

    # Get battery status
    battery = master.recv_match(type='BATTERY_STATUS', blocking=True)

    if battery and battery.voltages:
        valid_voltages = [v for v in battery.voltages if v != 65535]
        
        if valid_voltages:
            voltage = valid_voltages[0] / 1000.0  # Convert millivolts to volts
            print(f"Battery voltage: {voltage:.2f}V")
            client.publish("vehicle/battery_voltage", voltage)
        else:
            print("No valid battery voltage readings.")
    else:
        print("Battery status not available or invalid data.")

# Main loop to periodically set system time and publish telemetry data
try:
    # Create a new MQTT client connection
    client = mqtt.Client()
    client.connect(mqtt_broker)

    while True:
        set_system_time()

        # Publish telemetry data
        publish_telemetry(client)

        time.sleep(5)  # Adjust the frequency of data collection as needed

except KeyboardInterrupt:
    print("Exiting...")

finally:
    # Close the MAVLink connection and MQTT client
    master.close()
    client.disconnect()

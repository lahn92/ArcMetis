#
# This script wil handle the coordination of mesurements by the probe. 
# it reads probe depths and times from a file on the ARCMETIS usb drive and then modifies the MQTT winchsetpoint. 
# It starts the mission based on the status of the boat by looking at status/init_sampling, platform/mode, and platform/gps_speed
# the script also controles the probe by sending UDP messages. 
#

import time
import paho.mqtt.client as mqtt
import threading
import socket

# USB base path
usb_base_path = '/media/arcmetis/ARCMETIS/'
file_name = 'depths_times.txt'  # File containing depths and times
file_path = usb_base_path + file_name

# MQTT Configuration
broker_address = "127.0.0.1"
setpoint_topic = "platform/winchSetPoint"
sonar_depth_topic = "platform/sonarDepth"
init_sampling_topic = "status/init_sampling"

# UDP Server Configuration
server_ip = '192.168.1.63'
server_port = 61556

# Global variables for state and sonar depth limit
sonar_depth_limit = float('inf')  # Default to no limit
state = "idle"  # Possible states: "idle", "sampling", "waiting"
depths_and_times = []  # List to hold depths and times
current_index = 0  # Index of the current depth-time pair

# UDP socket setup
udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


# Send UDP messages
def send_udp_message(message):
    try:
        udp_socket.sendto(message.encode(), (server_ip, server_port))
        print(f"Sent UDP message: {message}")
    except Exception as e:
        print(f"Failed to send UDP message: {e}")


# Callback for sonar depth updates
def on_message(client, userdata, message):
    global sonar_depth_limit, state, current_index, depths_and_times

    if message.topic == sonar_depth_topic:
        try:
            sonar_depth = float(message.payload.decode())
            sonar_depth_limit = sonar_depth - 2  # Apply 2-meter safety buffer
            print(f"Updated sonar depth limit: {sonar_depth_limit} meters")
            if not depths_and_times:
                generate_default_depths()  # Generate default depths based on updated limit
        except ValueError:
            print("Invalid sonar depth value received")
    
    elif message.topic == init_sampling_topic:
        try:
            init_value = int(message.payload.decode())
            if init_value == 1 and state != "sampling":
                print("Switching to sampling state.")
                state = "sampling"
                current_index = 0  # Restart sampling from the first depth
                send_udp_message("on")  # Notify server sampling has started
            elif init_value == 0 and state != "idle":
                print("Switching to idle state.")
                state = "idle"
                send_udp_message("stop")  # Notify server sampling has stopped
        except ValueError:
            print("Invalid init sampling value received")


# Function to listen to MQTT topics
def mqtt_listen():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(broker_address)
    client.subscribe([(sonar_depth_topic, 0), (init_sampling_topic, 0)])
    print("Listening to MQTT topics...")
    client.loop_forever()


# Read depths and times from the file
def read_depths_and_times(file_path):
    try:
        with open(file_path, 'r') as file:
            data = []
            for line in file:
                parts = line.strip().split()
                if len(parts) == 2:
                    depth = float(parts[0])  # Depth in meters
                    time_in_min = float(parts[1])  # Time in minutes
                    data.append((depth, time_in_min))
            return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []


# Generate default depths based on sonar depth limit
def generate_default_depths():
    global depths_and_times, sonar_depth_limit
    if sonar_depth_limit == float('inf'):
        print("Sonar depth limit not set. Cannot generate default depths.")
        return

    depths_and_times = []
    depth = 0
    while depth + 5 <= sonar_depth_limit:  # Increment by 5 meters
        depths_and_times.append((depth, 10))  # Time is 10 minutes for each depth
        depth += 5

    print(f"Generated default depths up to {sonar_depth_limit - 2} meters with a 2-meter safety buffer:")
    print(depths_and_times)


# Publish depths in the sampling state
def sampling_loop(client):
    global state, current_index

    while True:
        if state == "sampling" and current_index < len(depths_and_times):
            # Get the current depth and time
            depth, time_in_min = depths_and_times[current_index]
            safe_depth = min(depth, sonar_depth_limit)
            safe_depth_cm = int(safe_depth * 100)  # Convert meters to centimeters
            print(f"Publishing depth {safe_depth_cm} cm (index {current_index}).")
            client.publish(setpoint_topic, safe_depth_cm)

            # Wait for the duration specified
            time.sleep(time_in_min * 60)
            current_index += 1

        elif state == "sampling" and current_index >= len(depths_and_times):
            # All depths are processed; enter waiting state
            print("All depths processed. Entering waiting state. Sending setpoint 0.")
            state = "waiting"
            client.publish(setpoint_topic, 0)

        elif state == "waiting":
            # In waiting state, publish 0 regularly
            print("Waiting state: Publishing depth 0 cm.")
            client.publish(setpoint_topic, 0)
            time.sleep(10)  # Regular interval for waiting

        elif state == "idle":
            # In idle state, publish 0 regularly
            print("Idle state: Publishing depth 0 cm.")
            client.publish(setpoint_topic, 0)
            time.sleep(10)  # Regular interval for idle publishing

        else:
            time.sleep(1)  # Check the state periodically


# Main function
def main():
    global depths_and_times

    # Read depths and times from the file
    depths_and_times = read_depths_and_times(file_path)

    if not depths_and_times:
        print("No valid file data. Generating default depths...")
        generate_default_depths()

    # Start MQTT listener in a separate thread
    threading.Thread(target=mqtt_listen, daemon=True).start()

    # Connect to MQTT broker for publishing
    client = mqtt.Client()
    client.connect(broker_address)

    # Start the sampling loop
    sampling_loop(client)


if __name__ == "__main__":
    main()

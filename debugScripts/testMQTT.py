import paho.mqtt.client as mqtt
import random
import time
import threading

# MQTT Broker address
BROKER = "192.168.150.165"

# MQTT Topics
TOPICS = {
    "probe/tidGaaet": None,
    "probe/P_ude": None,
    "probe/P_inde": None,
    "probe/RH": None,
    "probe/SCD30_temp": None,
    "probe/htu_temp": None,
    "probe/T_ude": None,
    "probe/CO2": None,
    "probe/O2": None,
    "probe/CH4": None,
    "probe/MIPEX": None,
    "probe/EC": None,
    "probe/Perc_bat": None,
    "probe/P_diff": None
}

# Initialize MQTT client
client = mqtt.Client()

# Connection flag
is_connected = False

# User-defined mode
def select_mode():
    print("Select mode:")
    print("1: Send full data set")
    print("2: Send partial data set (selected topics)")
    mode = input("Enter your choice (1 or 2): ")
    return mode

# Generate random data for each topic except tidGaaet
def generate_random_data():
    return {
        "probe/P_ude": round(random.uniform(1000, 2000), 2),
        "probe/P_inde": round(random.uniform(1000, 2000), 2),
        "probe/RH": round(random.uniform(30, 60), 2),
        "probe/SCD30_temp": round(random.uniform(18, 30), 2),
        "probe/htu_temp": round(random.uniform(18, 30), 2),
        "probe/T_ude": round(random.uniform(20, 40), 2),
        "probe/CO2": round(random.uniform(300, 1000), 2),
        "probe/O2": round(random.uniform(20, 22), 2),
        "probe/CH4": round(random.uniform(0, 10), 2),
        "probe/MIPEX": round(random.uniform(0, 10), 2),
        "probe/EC": round(random.uniform(0, 1), 2),
        "probe/Perc_bat": round(random.uniform(0, 100), 2),
        "probe/P_diff": round(random.uniform(0, 10), 2)
    }

# Publish data to MQTT broker
def publish_data(mode):
    tidGaaet_counter = 0
    while is_connected:
        # Update tidGaaet with incremented counter
        TOPICS["probe/tidGaaet"] = tidGaaet_counter
        tidGaaet_counter += 1
        
        # Generate random data for other topics
        random_data = generate_random_data()

        # Select data to send based on the mode
        if mode == "1":
            # Full data set
            topics_to_publish = {**TOPICS, **random_data}
        elif mode == "2":
            # Partial data set (specific topics)
            topics_to_publish = {
                "probe/tidGaaet": TOPICS["probe/tidGaaet"],
                "probe/P_ude": random_data["probe/P_ude"],
                "probe/Perc_bat": random_data["probe/Perc_bat"],
            }
        else:
            print("Invalid mode selected. Exiting...")
            break

        # Publish data to MQTT broker
        for topic, value in topics_to_publish.items():
            client.publish(topic, value)
            print(f"Published {topic}: {value}")

        # Wait for a second before sending the next set of data
        time.sleep(5)

# Connect to MQTT broker
def on_connect(client, userdata, flags, rc):
    global is_connected
    if rc == 0:
        is_connected = True
        print(f"Connected to MQTT broker with result code {rc}")
        # Start publishing data after connecting in a separate thread
        publish_thread = threading.Thread(target=publish_data, args=(mode,))
        publish_thread.start()
    else:
        print(f"Failed to connect with result code {rc}")

# Setup the MQTT client and callbacks
client.on_connect = on_connect

# Select mode before connecting
mode = select_mode()

# Connect to the MQTT broker
client.connect(BROKER, keepalive=60)

# Start the MQTT loop to handle messages
client.loop_start()

try:
    # Run the script indefinitely
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    print("Script interrupted, exiting...")
finally:
    client.loop_stop()

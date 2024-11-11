import paho.mqtt.client as mqtt
import random
import time

# MQTT Broker address
BROKER = "127.0.0.1"

# MQTT Topics
TOPICS = {
    "topic/tidGaaet": None,
    "topic/P_ude": None,
    "topic/P_inde": None,
    "topic/RH": None,
    "topic/SCD30_temp": None,
    "topic/htu_temp": None,
    "topic/T_ude": None,
    "topic/CO2": None,
    "topic/O2": None,
    "topic/CH4": None,
    "topic/MIPEX": None,
    "topic/EC": None,
    "topic/Perc_bat": None,
    "topic/P_diff": None
}

# Initialize MQTT client
client = mqtt.Client()

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
        "topic/P_ude": round(random.uniform(1000, 2000), 2),
        "topic/P_inde": round(random.uniform(1000, 2000), 2),
        "topic/RH": round(random.uniform(30, 60), 2),
        "topic/SCD30_temp": round(random.uniform(18, 30), 2),
        "topic/htu_temp": round(random.uniform(18, 30), 2),
        "topic/T_ude": round(random.uniform(20, 40), 2),
        "topic/CO2": round(random.uniform(300, 1000), 2),
        "topic/O2": round(random.uniform(20, 22), 2),
        "topic/CH4": round(random.uniform(0, 10), 2),
        "topic/MIPEX": round(random.uniform(0, 10), 2),
        "topic/EC": round(random.uniform(0, 1), 2),
        "topic/Perc_bat": round(random.uniform(0, 100), 2),
        "topic/P_diff": round(random.uniform(0, 10), 2)
    }

# Publish data to MQTT broker
def publish_data(mode):
    tidGaaet_counter = 0
    while True:
        # Update tidGaaet with incremented counter
        TOPICS["topic/tidGaaet"] = tidGaaet_counter
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
                "topic/tidGaaet": TOPICS["topic/tidGaaet"],
                "topic/P_ude": random_data["topic/P_ude"],
                "topic/Perc_bat": random_data["topic/Perc_bat"],
                "topic/tidGaaet": TOPICS["topic/tidGaaet"]
            }
        else:
            print("Invalid mode selected. Exiting...")
            break

        # Publish data to MQTT broker
        for topic, value in topics_to_publish.items():
            client.publish(topic, value)
            print(f"Published {topic}: {value}")

        # Wait for a second before sending the next set of data
        time.sleep(1)

# Connect to MQTT broker
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with result code {rc}")
    # Start publishing data after connecting
    mode = select_mode()
    publish_data(mode)

# Setup the MQTT client and callbacks
client.on_connect = on_connect

# Connect to the MQTT broker
client.connect(BROKER, keepalive=60)

# Start the MQTT loop to handle messages
client.loop_start()

try:
    # Run the script indefinitely
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Script interrupted, exiting...")
finally:
    client.loop_stop()

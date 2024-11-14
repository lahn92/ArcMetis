import paho.mqtt.client as mqtt

# Configuration
mqtt_broker = '192.168.225.165'  # Replace with your MQTT broker's IP
mqtt_topics = [
    "platform/mode",
    "platform/battery_voltage",
    "platform/gps_latitude",
    "platform/gps_longitude",
    "platform/gps_altitude",
    "platform/arming_status",
    "platform/system_status",
    "platform/gps_speed",
    "platform/battery_current",
    "platform/heading"
]

# Callback for when the client connects to the broker
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    # Subscribe to all topics
    for topic in mqtt_topics:
        client.subscribe(topic)
        print(f"Subscribed to {topic}")

# Callback for when a message is received
def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic} - Message: {msg.payload.decode()}")

# Set up MQTT client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect(mqtt_broker)

# Start listening in a blocking loop
client.loop_forever()

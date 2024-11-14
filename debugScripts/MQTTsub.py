import paho.mqtt.client as mqtt

# MQTT Broker address
mqtt_broker = 'arcmetis.local'  # Replace with your broker's IP
mqtt_topic = 'status/alarms'

# Define on_connect callback
def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(mqtt_topic)

# Define on_message callback
def on_message(client, userdata, msg):
    print(f"Received message from topic {msg.topic}: {msg.payload.decode()}")

# Create an MQTT client instance
client = mqtt.Client()

# Attach the callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the MQTT broker
client.connect(mqtt_broker)

# Start the network loop and wait for messages
client.loop_forever()

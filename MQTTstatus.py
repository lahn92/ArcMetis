#This script handles any alerts reported over MQTT and sendes/cycles the alerts to the status topic to by showen on the dashboard. 

import paho.mqtt.client as mqtt
import time

# MQTT setup
BROKER_IP = "127.0.0.1"  # Change this to your broker IP if needed
STATUS_TOPIC = "status/alarms"
ALERT_TOPICS = [
    "probe/leak",  # Add more topics as needed to this list. the topics should be 0 for no fault and 1 for fault. they also needs to be added to the grafana server dashboard status panel vis. 
]
TOPIC_ALERT_STATUS = {}  # Stores status numbers for each topic
current_alerts = []
alert_index = 0

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully to MQTT broker.")
        # Subscribe to all alert topics
        for topic in ALERT_TOPICS:
            client.subscribe(topic)
    else:
        print(f"Failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc):
    print("Disconnected from MQTT broker. Attempting to reconnect...")
    while True:
        try:
            client.reconnect()
            print("Reconnected to MQTT broker.")
            break
        except Exception as e:
            print(f"Reconnection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def on_message(client, userdata, msg):
    topic = msg.topic
    try:
        payload = round(float(msg.payload.decode()))
    except ValueError:
        print(f"Received non-numeric payload: {msg.payload}")
        return

    # Check for active alert
    if payload == 1:
        if topic not in TOPIC_ALERT_STATUS:
            TOPIC_ALERT_STATUS[topic] = len(TOPIC_ALERT_STATUS) + 1
        if topic not in current_alerts:
            current_alerts.append(topic)
    else:
        if topic in current_alerts:
            current_alerts.remove(topic)


def main():
    global alert_index
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        client.connect(BROKER_IP)
    except Exception as e:
        print(f"Initial connection failed: {e}")
        client.reconnect()

    client.loop_start()

    no_alerts_sent = False  # Tracks if "0" has already been sent for no alerts

    while True:
        if current_alerts:
            # Reset no_alerts_sent and cycle through active alerts
            no_alerts_sent = False
            active_topic = current_alerts[alert_index % len(current_alerts)]
            client.publish(STATUS_TOPIC, TOPIC_ALERT_STATUS[active_topic])
            alert_index += 1
        else:
            # Send "0" only once when there are no active alerts
            if not no_alerts_sent:
                client.publish(STATUS_TOPIC, 0)
                no_alerts_sent = True

        time.sleep(1)

if __name__ == "__main__":
    main()

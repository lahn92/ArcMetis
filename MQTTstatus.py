import paho.mqtt.client as mqtt
import time

# MQTT setup
BROKER_IP = "127.0.0.1"  # Adjust if needed
STATUS_TOPIC = "status/alarms"
ALERT_TOPICS = ["status/noUSB", 
                "probe/leak",]
TOPIC_ALERT_STATUS = {}  # Stores status numbers for each topic
current_alerts = []
alert_index = 0

MAX_RETRIES = 5  # Maximum number of retries
RETRY_INTERVAL = 5  # Time (in seconds) between retries

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected successfully to MQTT broker.")
        for topic in ALERT_TOPICS:
            client.subscribe(topic)
            print(f"Subscribed to {topic}")
    else:
        print(f"Failed to connect, return code {rc}")

def on_disconnect(client, userdata, rc):
    print("Disconnected from MQTT broker. Attempting to reconnect...")
    retry_count = 0
    while retry_count < MAX_RETRIES:
        try:
            client.reconnect()
            print("Reconnected to MQTT broker.")
            break
        except Exception as e:
            retry_count += 1
            print(f"Reconnection attempt {retry_count} failed: {e}. Retrying in {RETRY_INTERVAL} seconds...")
            time.sleep(RETRY_INTERVAL)
    if retry_count == MAX_RETRIES:
        print("Maximum retries reached. Could not reconnect to MQTT broker.")

def on_message(client, userdata, msg):
    topic = msg.topic
    try:
        payload = round(float(msg.payload.decode()))
        print(f"Received message on {topic}: {payload}")
    except ValueError:
        print(f"Received non-numeric payload: {msg.payload}")
        return

    if payload == 1:
        if topic not in TOPIC_ALERT_STATUS:
            TOPIC_ALERT_STATUS[topic] = len(TOPIC_ALERT_STATUS) + 1
        if topic not in current_alerts:
            current_alerts.append(topic)
            print(f"Alert added for topic {topic}, current alerts: {current_alerts}")
    else:
        if topic in current_alerts:
            current_alerts.remove(topic)
            print(f"Alert removed for topic {topic}, current alerts: {current_alerts}")

def main():
    global alert_index
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message

    try:
        client.connect(BROKER_IP, keepalive=60)
    except Exception as e:
        print(f"Initial connection failed: {e}")
        client.reconnect()

    client.loop_start()

    no_alerts_sent = False

    while True:
        if current_alerts:
            no_alerts_sent = False
            active_topic = current_alerts[alert_index % len(current_alerts)]
            status = TOPIC_ALERT_STATUS[active_topic]
            print(f"Publishing alert status {status} for topic {active_topic}")
            client.publish(STATUS_TOPIC, status)
            alert_index += 1
        else:
            if not no_alerts_sent:
                print("Publishing no alert status (0)")
                client.publish(STATUS_TOPIC, 0)
                no_alerts_sent = True

        time.sleep(1)

if __name__ == "__main__":
    main()

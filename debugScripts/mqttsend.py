import paho.mqtt.client as mqtt

# MQTT Settings
mqtt_broker = '192.168.150.165'  # IP address of the MQTT broker
topics = [
    'status/noUSB',
    'probe/leak',
    'platform/winchSetPoint',
    'probe/tidGaaet',
    'platform/winchCurrentPos',
    'status/logging',
]

def main():
    # Set up MQTT client
    client = mqtt.Client()
    client.connect(mqtt_broker, keepalive=60)

    try:
        while True:
            # Display available topics
            print("\nAvailable topics:")
            for i, topic in enumerate(topics, 1):
                print(f"{i}. {topic}")
            
            # Prompt for topic
            topic_choice = input("Select a topic by number, or type a new topic: ").strip()
            if topic_choice.isdigit() and 1 <= int(topic_choice) <= len(topics):
                mqtt_topic = topics[int(topic_choice) - 1]
            else:
                mqtt_topic = topic_choice  # Use custom topic

            # Prompt for value
            value_input = input(f"Enter value to send to '{mqtt_topic}', or type 'exit' to quit: ").strip().lower()
            if value_input == 'exit':
                break

            try:
                value = float(value_input)
                client.publish(mqtt_topic, value)
                print(f"Sent value: {value} to MQTT topic '{mqtt_topic}'")
            except ValueError:
                print("Invalid input. Please enter a numeric value or 'exit'.")

    except KeyboardInterrupt:
        print("\nExiting sender script.")

    finally:
        client.disconnect()

if __name__ == '__main__':
    main()

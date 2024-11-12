import paho.mqtt.client as mqtt

# MQTT Settings
mqtt_broker = '192.168.150.165'  # Localhost IP as the broker is on the same Raspberry Pi
mqtt_topic = 'platform/winchSetPoint'
#probe/leak
#platform/winchSetPoint
#probe/tidGaaet
#platform/winchCurrentPos
def main():
    # Set up MQTT client
    client = mqtt.Client()
    client.connect(mqtt_broker, keepalive=60)
    
    try:
        while True:
            user_input = input("Enter target position in cm, or 'exit' to quit: ").strip().lower()
            if user_input == 'exit':
                break
            
            try:
                target_position = float(user_input)
                client.publish(mqtt_topic, target_position)
                print(f"Sent target position: {target_position} cm to MQTT topic '{mqtt_topic}'")
            except ValueError:
                print("Invalid input. Please enter a numeric value for position or 'exit'.")
    
    except KeyboardInterrupt:
        print("Exiting sender script.")
    
    finally:
        client.disconnect()

if __name__ == '__main__':
    main()

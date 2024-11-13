#this script read the Blue Robotics ping 1d and sende the data to the MQTT broker. 

from brping import Ping1D
import time
import paho.mqtt.client as mqtt

# Hardcoded settings
DEVICE_PORT = '/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_AB0JJR9I-if00-port0'
BAUDRATE = 115200
MQTT_BROKER = '127.0.0.1'  # MQTT broker address

# Function to connect to the MQTT broker
def connect_mqtt():
    while True:
        try:
            mqtt_client.connect(MQTT_BROKER, keepalive=60)  # Re-added keepalive
            mqtt_client.loop_start()  # Start the loop to process callbacks
            print("Connected to MQTT broker")
            break
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}. Retrying in 5 seconds...")
            time.sleep(5)

# Make a new Ping
myPing = Ping1D()
myPing.connect_serial(DEVICE_PORT, BAUDRATE)

if myPing.initialize() is False:
    print("Failed to initialize Ping!")
    exit(1)

myPing.set_speed_of_sound(1450000) #for more accrute mesurement change this to match the medium [mm/s]
# Initialize MQTT client
mqtt_client = mqtt.Client()

# Connect to the MQTT broker with retry
connect_mqtt()

print("------------------------------------")
print("Starting Ping...")
print("------------------------------------")

# Read and print distance measurements with confidence
try:
    while True:
        data = myPing.get_distance()
        if data:
            distance = data["distance"]
            confidence = data["confidence"]
            print("Distance: %s\tConfidence: %s%%" % (distance, confidence))
            
            # Publish the depth to the MQTT topic
            mqtt_client.publish("platform/sonarDepth", distance)
        else:
            print("Failed to get distance data")
        
        time.sleep(5)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    mqtt_client.loop_stop()  # Stop the loop
    mqtt_client.disconnect()

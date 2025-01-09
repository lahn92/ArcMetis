#this script takes in data from the probe over the UDP connection and sends it to the mqtt broker. 

import socket
import paho.mqtt.client as mqtt
import time

# Set up UDP server with socket timeout handling
def udp_server(host='0.0.0.0', port=61557, buffer_size=1024, mqtt_broker='127.0.0.1'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))

    # Set a timeout of 10 seconds to prevent the socket from hanging indefinitely
    sock.settimeout(10)
    
    print(f"Listening for UDP packets on {host}:{port}...")

    client = mqtt.Client()

    while True:
        try:
            data, addr = sock.recvfrom(buffer_size)
            print(f"Received message from {addr}: {data.decode()}")
            process_data(data.decode(), client, mqtt_broker)

        except socket.timeout:
            # Timeout reached, no packet received, continue listening
            print("No UDP packet received, waiting...")
            continue  # Continue the loop and wait for the next packet
        
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)  # Wait a bit before retrying in case of other errors

def process_data(data, client, mqtt_broker):
    try:
        # Split the received data into parts and strip whitespace from each value
        values = [value.strip() for value in data.split(',')]
        
        # Connect to the MQTT broker
        client.connect(mqtt_broker)
        
        # Print the number of values for debugging
        print(f"Number of values received: {len(values)}")
        
        if len(values) == 13:  # First packet format
            tidGaaet, P_ude, P_inde, RH, SCD30_temp, htu_temp, T_ude, CO2, O2, CH4, MIPEX, EC, Perc_bat = values
            P_diff = abs(float(P_ude) - float(P_inde))
            
            # Publish each value to its own MQTT topic
            client.publish("probe/P_ude", P_ude)
            client.publish("probe/P_inde", P_inde)
            client.publish("probe/RH", RH)
            client.publish("probe/SCD30_temp", SCD30_temp)
            client.publish("probe/htu_temp", htu_temp)
            client.publish("probe/T_ude", T_ude)
            client.publish("probe/CO2", CO2)
            client.publish("probe/O2", O2)
            client.publish("probe/CH4", CH4)
            client.publish("probe/MIPEX", MIPEX)
            client.publish("probe/EC", EC)
            client.publish("probe/Perc_bat", Perc_bat)
            client.publish("probe/P_diff", P_diff)
            client.publish("probe/tidGaaet", tidGaaet)

            print(f"Published first packet values to respective topics.")
        
        elif len(values) == 3:  # Second packet format
            tidGaaet, P_ude, Perc_bat = values
            
            # Publish to MQTT
            client.publish("probe/P_ude", P_ude)
            client.publish("probe/Perc_bat", Perc_bat)
            client.publish("probe/tidGaaet", tidGaaet)
            
            print(f"Published second packet values to respective topics.")
        
        elif 'leak' in data:  # Leak message
            # Convert leak message to boolean
            leak_status = 1 if 'leak' in data else 0
            client.publish("probe/leak", leak_status)
            print(f"Published to probe/leak: {leak_status}")
        
        # Disconnect from the MQTT broker
        client.disconnect()

    except Exception as e:
        print(f"Error processing data or publishing to MQTT: {e}")

# Run the UDP server
udp_server()

from pymavlink import mavutil
import time

# Connection string (adjust for your system)
connection_string = '/dev/ttyACM0'
baud_rate = 57600

# Create a connection to the vehicle
master = mavutil.mavlink_connection(connection_string, baud=baud_rate)

# Wait for the first heartbeat
print("Waiting for heartbeat...")
master.wait_heartbeat()
print("Heartbeat from vehicle (system_id: {}, component_id: {})".format(master.target_system, master.target_component))

# Get vehicle mode
mode = master.flightmode
print("Current mode: {}".format(mode))

# Get battery status
battery = master.recv_match(type='BATTERY_STATUS', blocking=True)

# Process the battery voltage, ensuring valid values
if battery and battery.voltages:
    # Filter out invalid readings (65535 is a common 'invalid' marker in MAVLink)
    valid_voltages = [v for v in battery.voltages if v != 65535]
    
    if valid_voltages:
        # Assuming you're interested in the first valid voltage
        voltage = valid_voltages[0] / 1000.0  # Convert millivolts to volts
        print(f"Battery voltage: {voltage:.2f}V")
    else:
        print("No valid battery voltage readings.")
else:
    print("Battery status not available or invalid data.")

# Get the current UTC time from the GPS
system_time = master.recv_match(type='SYSTEM_TIME', blocking=True)
if system_time and system_time.time_unix_usec > 0:
    utc_time = system_time.time_unix_usec / 1e6  # Convert microseconds to seconds
    utc_time_struct = time.gmtime(utc_time)  # Convert to struct_time for formatting
    utc_time_str = time.strftime('%Y-%m-%d %H:%M:%S', utc_time_struct)
    print(f"UTC Time from GPS: {utc_time_str}")
else:
    print("No valid GPS time available.")

# Close the connection
master.close()

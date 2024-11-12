import paho.mqtt.client as mqtt
from gpiozero import PWMOutputDevice, DigitalOutputDevice, DigitalInputDevice
from gpiozero.pins.pigpio import PiGPIOFactory
import time

# Pin Definitions
PWM_PIN = 13         # PWM pin for speed control
DIR_PIN = 6          # Direction pin
HALL_EFFECT_PIN = 10 # Hall effect sensor pin
ENCODER_A_PIN = 8    # Encoder A channel pin
bounce_time = 0.005
P_factor = 0.02 

# Motor and Encoder Configuration
invert_direction = True    # Set to True to invert the motor direction
PWM_FREQUENCY = 5000      # Set desired PWM frequency in Hz
MOTOR_SPEED = 0.5         # Normal motor speed (0.0 to 1.0)
HOMING_SPEED = 0.5        # Slower speed for homing (0.0 to 1.0)

# Encoder Specifications
PULSES_PER_REVOLUTION = 100  # Encoder PPR
DISTANCE_PER_PULSE = 0.2638  # Distance per encoder pulse in cm

# MQTT Settings
mqtt_broker = '127.0.0.1'
mqtt_topic = 'platform/winchSetPoint'
status_topic = 'platform/winchCurrentPos'
RECONNECT_ATTEMPTS = 5      # Max number of reconnect attempts

# Define the pin factory using pigpio
pin_factory = PiGPIOFactory()

# Initialize the motor and sensor
pwm_motor = PWMOutputDevice(PWM_PIN, frequency=PWM_FREQUENCY, pin_factory=pin_factory)
direction_pin = DigitalOutputDevice(DIR_PIN, pin_factory=pin_factory)
hall_effect_sensor = DigitalInputDevice(HALL_EFFECT_PIN, pull_up=True, pin_factory=pin_factory)

# Initialize encoder channel A only
encoder_a = DigitalInputDevice(ENCODER_A_PIN, pull_up=False, bounce_time=bounce_time, pin_factory=pin_factory)

# Encoder state
position_pulses = 0
current_direction = 'up'  # Track current motor direction

def encoder_callback():
    global position_pulses, current_direction
    
    # Increment or decrement based on current motor direction
    if current_direction == 'down':
        position_pulses += 1
    else:  # direction is 'up'
        position_pulses -= 1

# Only attach to rising edge (when_activated)
encoder_a.when_activated = encoder_callback

def get_position_cm():
    """Calculates the current position in cm from pulses."""
    return position_pulses * DISTANCE_PER_PULSE

def home_motor(client):
    """Moves the motor 'up' to the home position using the hall effect sensor."""
    print("Homing motor...")
    global current_direction
    
    current_direction = 'up'
    if invert_direction:
        direction_pin.off()
    else:
        direction_pin.on()
    
    pwm_motor.value = HOMING_SPEED  # Use homing speed

    while not hall_effect_sensor.is_active:
        time.sleep(0.01)

    pwm_motor.off()
    global position_pulses
    position_pulses = 0
    print("Motor homed to zero position.")
    client.publish(status_topic, (get_position_cm()/100))

def move_to_position(client, target_cm):
    """Moves the motor to a specified position in cm."""
    print(f"Moving to target position: {target_cm} cm")
    global current_direction

    if target_cm < 0:
        print("Target position cannot be negative.")
        return

    current_position = get_position_cm()

    # Determine direction based on target position
    if target_cm > current_position:
        current_direction = 'down'  # Move down if target is greater than current
        client.publish(status_topic, -2)
    else:
        current_direction = 'up'    # Move up if target is less than current
        client.publish(status_topic, -1)

    print(f"Current Position: {current_position} cm, Direction: {current_direction}")

    # Start the motor based on the determined direction
    if current_direction == 'down':
        # Set direction for downward movement considering inversion
        direction_pin.on() if invert_direction else direction_pin.off()
        pwm_motor.value = MOTOR_SPEED  # Use normal motor speed
        print("Motor moving down")
    elif current_direction == 'up':
        if hall_effect_sensor.is_active:
            print("End-stop reached. Motor will not run up.")
            return
        # Set direction for upward movement considering inversion
        direction_pin.off() if invert_direction else direction_pin.on()
        pwm_motor.value = MOTOR_SPEED  # Use normal motor speed
        print("Motor moving up")

    # Continue until target position is reached
    while (current_direction == 'down' and current_position < target_cm) or \
          (current_direction == 'up' and current_position > target_cm):

        current_position = get_position_cm()  # Update current position
        print(f"Current Position: {current_position} cm")

        # Check for end-stop if moving up
        if current_direction == 'up' and hall_effect_sensor.is_active:
            print("End-stop reached. Cannot move further up.")
            break

        time.sleep(0.05)  # Short delay to avoid excessive CPU usage

    # Stop the motor after reaching the target or if end-stop is triggered
    pwm_motor.off()
    final_position = get_position_cm()
    print(f"Reached position: {final_position} cm at {position_pulses} pulses")
    client.publish(status_topic, (final_position/100))

def on_mqtt_message(client, userdata, message):
    """Callback function to handle MQTT messages."""
    try:
        target_position = float(message.payload.decode())
        print(f"Received target position: {target_position} cm from MQTT")
        
        if target_position == 0:
            home_motor(client)  # Home the motor if the setpoint is 0
        else:
            move_to_position(client, target_position)
    except ValueError:
        print("Invalid MQTT message: expected numeric target position")

def on_mqtt_disconnect(client, userdata, rc):
    """Handles disconnection from the MQTT broker."""
    print("Disconnected from MQTT broker.")
    
    # Attempt to reconnect up to RECONNECT_ATTEMPTS times
    for attempt in range(RECONNECT_ATTEMPTS):
        try:
            client.reconnect()
            print(f"Reconnected to MQTT broker on attempt {attempt + 1}")
            return
        except Exception as e:
            print(f"Reconnect attempt {attempt + 1} failed: {e}")
            time.sleep(1)
    
    # If unable to reconnect after initial connection, home the motor
    print("Failed to reconnect after multiple attempts. Homing the motor.")
    home_motor(client)

def main():
    # Set up MQTT client
    client = mqtt.Client()
    client.on_message = on_mqtt_message
    client.on_disconnect = on_mqtt_disconnect  # Set the disconnect callback

    # Attempt initial connection
    for attempt in range(RECONNECT_ATTEMPTS):
        try:
            client.connect(mqtt_broker, keepalive=60)
            print(f"Connected to MQTT broker on attempt {attempt + 1}")
            break
        except Exception as e:
            print(f"Failed to connect to MQTT broker (attempt {attempt + 1}): {e}")
            time.sleep(1)
    else:
        print("Failed to connect after multiple attempts. Exiting program.")
        return

    # Subscribe to the setpoint topic and start the MQTT loop
    client.subscribe(mqtt_topic)
    client.loop_start()

    try:
        home_motor(client)  # Initial homing at startup
        while True:
            time.sleep(1)  # Keep the program running to receive MQTT messages
    except KeyboardInterrupt:
        print("Exiting program.")
    finally:
        client.loop_stop()
        pwm_motor.close()

if __name__ == '__main__':
    main()

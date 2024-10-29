import paho.mqtt.client as mqtt
from gpiozero import PhaseEnableMotor, DigitalInputDevice
from gpiozero.pins.pigpio import PiGPIOFactory
import time

# Pin Definitions
PWM_PIN = 13         # Enable (PWM) pin for speed control
DIR_PIN = 6          # Phase (direction) pin
HALL_EFFECT_PIN = 10 # Hall effect sensor pin
ENCODER_A_PIN = 8    # Encoder A channel pin
ENCODER_B_PIN = 4    # Encoder B channel pin
bounce_time = 0.005

# Motor and Encoder Configuration
invert_direction = False  # Set to True to invert the motor direction

# Encoder Specifications
PULSES_PER_REVOLUTION = 100  # Encoder PPR
DISTANCE_PER_PULSE = 0.1286  # Distance per encoder pulse in cm

# MQTT Settings
mqtt_broker = '127.0.0.1'
mqtt_topic = 'winch/setpoint'

# Define the pin factory using pigpio
pin_factory = PiGPIOFactory()

# Initialize the motor and sensor
motor = PhaseEnableMotor(phase=DIR_PIN, enable=PWM_PIN, pwm=True, pin_factory=pin_factory)
hall_effect_sensor = DigitalInputDevice(HALL_EFFECT_PIN, pull_up=True, pin_factory=pin_factory)

# Initialize encoder channels
encoder_a = DigitalInputDevice(ENCODER_A_PIN, pull_up=False, bounce_time=bounce_time, pin_factory=pin_factory)
encoder_b = DigitalInputDevice(ENCODER_B_PIN, pull_up=False, bounce_time=bounce_time, pin_factory=pin_factory)

# Encoder state
position_pulses = 0
last_a_state = encoder_a.value

def encoder_callback():
    global position_pulses, last_a_state
    
    current_a = encoder_a.value
    
    if current_a != last_a_state:
        if current_a == encoder_b.value:
            position_pulses += 1
        else:
            position_pulses -= 1
                
        last_a_state = current_a

# Attach encoder callback to pin A
encoder_a.when_activated = encoder_callback
encoder_a.when_deactivated = encoder_callback

def get_position_cm():
    """Calculates the current position in cm from pulses."""
    return position_pulses * DISTANCE_PER_PULSE

def home_motor():
    """Moves the motor 'up' to the home position using the hall effect sensor."""
    print("Homing motor...")
    if invert_direction:
        motor.backward(speed=1)
    else:
        motor.forward(speed=1)
    
    while not hall_effect_sensor.is_active:
        time.sleep(0.01)

    motor.stop()
    global position_pulses
    position_pulses = 0
    print("Motor homed to zero position.")

def move_to_position(target_cm):
    """Moves the motor to a specified position in cm."""
    print(f"Moving to target position: {target_cm} cm")

    if target_cm < 0:
        print("Target position cannot be negative.")
        return

    current_position = get_position_cm()

    # Determine direction based on target position
    if target_cm > current_position:
        direction = 'down'  # Move down if target is greater than current
    else:
        direction = 'up'  # Move up if target is less than current

    print(f"Current Position: {current_position} cm, Direction: {direction}")

    # Start the motor based on the determined direction
    if direction == 'down':
        motor.backward(speed=1)  # Move motor down
        print("Motor moving down")
    elif direction == 'up':
        if hall_effect_sensor.is_active:
            print("End-stop reached. Motor will not run up.")
            return
        motor.forward(speed=1)  # Move motor up
        print("Motor moving up")

    # Continue until target position is reached
    while (direction == 'down' and current_position < target_cm) or \
          (direction == 'up' and current_position > target_cm):

        current_position = get_position_cm()  # Update current position
        print(f"Current Position: {current_position} cm")

        # Check for end-stop if moving up
        if direction == 'up' and hall_effect_sensor.is_active:
            print("End-stop reached. Cannot move further up.")
            break

        time.sleep(0.05)  # Short delay to avoid excessive CPU usage

    # Stop the motor after reaching the target or if end-stop is triggered
    motor.stop()
    print(f"Reached position: {get_position_cm()} cm")

def on_mqtt_message(client, userdata, message):
    """Callback function to handle MQTT messages."""
    try:
        target_position = float(message.payload.decode())
        print(f"Received target position: {target_position} cm from MQTT")
        
        if target_position == 0:
            home_motor()  # Home the motor if the setpoint is 0
        else:
            move_to_position(target_position)
    except ValueError:
        print("Invalid MQTT message: expected numeric target position")


def main():
    home_motor()

    # Set up MQTT client
    client = mqtt.Client()
    client.on_message = on_mqtt_message
    client.connect(mqtt_broker)

    # Subscribe to the setpoint topic
    client.subscribe(mqtt_topic)
    client.loop_start()

    try:
        while True:
            time.sleep(1)  # Keep the program running to receive MQTT messages
    except KeyboardInterrupt:
        print("Exiting program.")
    finally:
        client.loop_stop()
        motor.close()

if __name__ == '__main__':
    main()

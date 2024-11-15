import subprocess
import time

# Path to the virtual environment's Python executable
venv_python = '/home/arcmetis/ArcMetis/.venv/bin/python3'

# List of scripts to run, excluding MQTTstatus.py for now
scripts = [
    'UDPtoMQTT.py',
    'winchController.py',
    'MQTTtoLOG.py',
    'sonarToMQTT.py',
]
#'MAVtoMQTT.py',

# Start each script in parallel (except MQTTstatus.py)
processes = []
for script in scripts:
    process = subprocess.Popen([venv_python, script])
    processes.append(process)

# Delay for 30 seconds
time.sleep(30)

# Start MQTTstatus.py
mqtt_status_process = subprocess.Popen([venv_python, 'MQTTstatus.py'])
processes.append(mqtt_status_process)

# Optionally wait for all processes to complete
for process in processes:
    process.wait()

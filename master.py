import subprocess
import sys
import os

# Path to the virtual environment's Python executable
venv_python = '/home/arcmetis/ArcMetis/.venv/bin/python3'

# List of scripts to run
scripts = [
    'UDPtoMQTT.py',
    'MQTTstatus.py',
    'MQTTtoLOG.py',
    'sonarToMQTT.py',
    'MAVtoMQTT.py',
]
#    'winchController.py',
# Start each script in parallel
processes = []
for script in scripts:
    process = subprocess.Popen([venv_python, script])
    processes.append(process)

# Optionally wait for all processes to complete
for process in processes:
    process.wait()

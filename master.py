#This script will be used as the master scripts, that gets stated by a service file. and then starts all other scripts. 

import subprocess

# List of scripts to run
scripts = [
    'UDPtoMQTT.py',
    'winchController.py'
    'MQTTstatus.py'
]

# Start each script in parallel
processes = []
for script in scripts:
    process = subprocess.Popen(['python3', script])
    processes.append(process)

# Optionally wait for all processes to complete
for process in processes:
    process.wait()

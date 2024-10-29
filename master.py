import subprocess

# List of scripts to run
scripts = [
    'UDPtoMQTT.py',
    'winchController.py'
]

# Start each script in parallel
processes = []
for script in scripts:
    process = subprocess.Popen(['python3', script])
    processes.append(process)

# Optionally wait for all processes to complete
for process in processes:
    process.wait()

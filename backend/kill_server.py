import subprocess
import os

try:
    output = subprocess.check_output("netstat -ano | findstr :8000", shell=True).decode()
    lines = output.strip().split('\n')
    for line in lines:
        if "LISTENING" in line:
            parts = line.strip().split()
            pid = parts[-1]
            print(f"Killing PID {pid}")
            os.system(f"taskkill /F /PID {pid}")
except subprocess.CalledProcessError:
    print("No process found on port 8000")

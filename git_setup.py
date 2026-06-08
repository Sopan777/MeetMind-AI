import os
import subprocess

def run(cmd):
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("ERROR:", result.stderr)
    return result.returncode

run("git init")
run("git add .")
run('git commit -m "Initial commit of MeetingMind AI"')

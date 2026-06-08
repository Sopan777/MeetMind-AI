import subprocess
import sys
import threading
import time
import os

def stream_output(pipe, prefix=""):
    """Reads from a pipe line-by-line and prints to stdout with a prefix."""
    try:
        for line in iter(pipe.readline, ''):
            if not line:
                break
            print(f"{prefix}{line}", end="")
    finally:
        pipe.close()

def main():
    print("==================================================")
    print(" Starting MeetingMind AI Backends (Unified Mode)")
    print("==================================================")
    
    # We use the existing start.bat files so they handle the PYTHONNOUSERSITE isolation
    backend_bat = "start.bat"
    diarization_bat = "start.bat"
    
    # Start Main Backend
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    
    print("[SYSTEM] Launching Main Backend on port 8000...")
    p_main = subprocess.Popen(
        backend_bat,
        cwd="backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env
    )
    
    # Start Diarization Microservice
    print("[SYSTEM] Launching Diarization Microservice on port 8001...")
    p_diar = subprocess.Popen(
        diarization_bat,
        cwd="diarization_service",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env
    )
    
    # Create threads to stream the output to this terminal
    t_main = threading.Thread(target=stream_output, args=(p_main.stdout, "[MAIN] "))
    t_diar = threading.Thread(target=stream_output, args=(p_diar.stdout, "[DIAR] "))
    
    t_main.daemon = True
    t_diar.daemon = True
    
    t_main.start()
    t_diar.start()
    
    try:
        # Keep the main thread alive waiting for the subprocesses
        p_main.wait()
        p_diar.wait()
    except KeyboardInterrupt:
        print("\n[SYSTEM] Caught Ctrl+C. Shutting down all servers gracefully...")
        
        # Kill the child processes and their children on Windows
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p_main.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
            
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(p_diar.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
            
        print("[SYSTEM] Shutdown complete.")
        sys.exit(0)

if __name__ == "__main__":
    main()

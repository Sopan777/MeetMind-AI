import os
import signal
import psutil

def kill_port(port):
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            try:
                pid = conn.pid
                if pid:
                    p = psutil.Process(pid)
                    p.terminate()
                    print(f"Killed process {pid} on port {port}")
            except Exception as e:
                print(f"Error killing {conn.pid}: {e}")

kill_port(3000)

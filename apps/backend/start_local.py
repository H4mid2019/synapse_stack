"""
Local Development Startup Script
Starts all 4 backend services + proxy in separate processes
"""

import os
import signal
import subprocess
import sys
import time

processes = []


def cleanup(signum=None, frame=None):
    print("\nShutting down all services...")
    for proc in processes:
        proc.terminate()
    for proc in processes:
        proc.wait()
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def start_service(name, script, port):
    print(f"Starting {name} on port {port}...")
    env = os.environ.copy()
    env["PORT"] = str(port)
    proc = subprocess.Popen(
        [sys.executable, script],
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    processes.append(proc)
    return proc


if __name__ == "__main__":
    print("Starting local development environment")
    print("-" * 40)

    # Start backend services using unified app factory
    start_service("Read Service (Instance 1)", "app_factory.py", 6001)
    time.sleep(2)

    # Note: For second read instance, we'd need to pass 'read' arg
    # But app_factory.py defaults to 'read' when run directly
    env = os.environ.copy()
    env["PORT"] = "6011"
    proc = subprocess.Popen(
        [sys.executable, "app_factory.py", "read"],
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    processes.append(proc)
    time.sleep(2)

    # Start write service
    env = os.environ.copy()
    env["PORT"] = "6002"
    proc = subprocess.Popen(
        [sys.executable, "app_factory.py", "write"],
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    processes.append(proc)
    time.sleep(2)

    # Start operations service
    env = os.environ.copy()
    env["PORT"] = "6003"
    proc = subprocess.Popen(
        [sys.executable, "app_factory.py", "operations"],
        env=env,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    processes.append(proc)
    time.sleep(2)

    # Start proxy
    print("Starting Reverse Proxy on port 5000...")
    proxy_proc = subprocess.Popen(
        [sys.executable, "local_proxy.py"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )
    processes.append(proxy_proc)

    print("\nAll services running:")
    print("Read Service (1):    http://localhost:6001")
    print("Read Service (2):    http://localhost:6011")
    print("Write Service:       http://localhost:6002")
    print("Operations Service:  http://localhost:6003")
    print("Reverse Proxy:       http://localhost:5000  <-- Use this")
    print("\nPress Ctrl+C to stop all services\n")

    # Wait for all processes
    try:
        for proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        cleanup()

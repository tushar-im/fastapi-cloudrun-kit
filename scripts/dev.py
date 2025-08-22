#!/usr/bin/env python3
"""
Development server script with Firebase emulator support.
"""

import os
import sys
import asyncio
import subprocess
import signal
import time
from pathlib import Path


def run_command(command: list, cwd: str = None, env: dict = None):
    """Run a command with proper error handling."""
    try:
        if env:
            env_vars = os.environ.copy()
            env_vars.update(env)
        else:
            env_vars = os.environ

        return subprocess.Popen(
            command,
            cwd=cwd,
            env=env_vars,
            stdout=None,
            stderr=None,
            text=True,
        )
    except Exception as e:
        print(f"Error running command {' '.join(command)}: {e}")
        return None


def check_firebase_emulators():
    """Check if Firebase emulators are running."""
    try:
        import requests

        response = requests.get("http://localhost:4000", timeout=2)
        return response.status_code == 200
    except:
        return False


def start_firebase_emulators():
    """Start Firebase emulators."""
    print("Starting Firebase emulators...")

    firebase_dir = Path("firebase")
    if not firebase_dir.exists():
        print("Firebase directory not found. Please ensure firebase/ directory exists.")
        return None

    # Check if firebase CLI is available
    try:
        subprocess.run(["firebase", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Firebase CLI not found. Please install it:")
        print("npm install -g firebase-tools")
        return None

    # Start emulators
    process = run_command(
        ["firebase", "emulators:start", "--project", "demo-project"], cwd="firebase"
    )

    if process:
        # Wait for emulators to start
        print("Waiting for Firebase emulators to start...")
        for _ in range(30):  # Wait up to 30 seconds
            if check_firebase_emulators():
                print("✅ Firebase emulators started successfully")
                return process
            time.sleep(1)

        print("⚠️  Firebase emulators may still be starting...")
        return process

    return None


def start_dev_server():
    """Start the FastAPI development server."""
    print("Starting FastAPI development server...")

    # Set development environment variables
    dev_env = {
        "ENVIRONMENT": "development",
        "DEBUG": "true",
        "RELOAD": "true",
        "USE_FIREBASE_EMULATOR": "true",
        "FIREBASE_AUTH_EMULATOR_HOST": "localhost:9099",
        "FIRESTORE_EMULATOR_HOST": "localhost:8080",
        "FIREBASE_STORAGE_EMULATOR_HOST": "localhost:9199",
        "FIREBASE_PROJECT_ID": "demo-project",
        "SECRET_KEY": "development-secret-key-not-for-production",
        "LOG_LEVEL": "DEBUG",
        "LOG_FORMAT": "console",
    }

    return run_command(
        [
            "python",
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
            "--reload",
        ],
        env=dev_env,
    )


def main():
    """Main development server function."""
    print("🚀 Starting FastAPI CloudRun Kit Development Environment")
    print("=" * 60)

    processes = []

    try:
        # Check if we should start Firebase emulators
        start_emulators = "--no-firebase" not in sys.argv

        if start_emulators:
            # Start Firebase emulators
            firebase_process = start_firebase_emulators()
            if firebase_process:
                processes.append(("Firebase Emulators", firebase_process))
            else:
                print("❌ Failed to start Firebase emulators")
                if "--firebase-required" in sys.argv:
                    print("Exiting because Firebase emulators are required")
                    return 1
                else:
                    print("Continuing without Firebase emulators...")

        # Start FastAPI server
        api_process = start_dev_server()
        if api_process:
            processes.append(("FastAPI Server", api_process))
            print("✅ FastAPI development server started")
        else:
            print("❌ Failed to start FastAPI server")
            return 1

        print("\n🎉 Development environment is ready!")
        print("-" * 40)
        print("🌐 FastAPI Server: http://localhost:8000")
        print("📚 API Documentation: http://localhost:8000/docs")
        print("🔧 Alternative Docs: http://localhost:8000/redoc")

        if start_emulators:
            print("🔥 Firebase Emulator UI: http://localhost:4000")
            print("🔐 Auth Emulator: http://localhost:9099")
            print("📦 Firestore Emulator: http://localhost:8080")
            print("📁 Storage Emulator: http://localhost:9199")

        print("-" * 40)
        print("Press Ctrl+C to stop all services")

        # Wait for processes
        try:
            while True:
                time.sleep(1)

                # Check if any process has died
                for name, process in processes:
                    if process.poll() is not None:
                        print(f"⚠️  {name} process has stopped")

        except KeyboardInterrupt:
            print("\n🛑 Shutting down development environment...")

    finally:
        # Clean up processes
        for name, process in processes:
            if process.poll() is None:
                print(f"Stopping {name}...")
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                except:
                    pass

        print("✅ All services stopped")
        return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

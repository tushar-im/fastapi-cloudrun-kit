#!/usr/bin/env python3
"""
Firebase emulator management script.
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path


def run_command(command: list, cwd: str = None, check: bool = True):
    """Run a command with proper error handling."""
    try:
        result = subprocess.run(
            command, cwd=cwd, check=check, capture_output=True, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(command)}: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return None
    except FileNotFoundError:
        print(f"Command not found: {command[0]}")
        return None


def check_firebase_cli():
    """Check if Firebase CLI is installed."""
    result = run_command(["firebase", "--version"], check=False)
    return result is not None


def install_firebase_cli():
    """Install Firebase CLI via npm."""
    print("Installing Firebase CLI...")
    result = run_command(["npm", "install", "-g", "firebase-tools"])
    return result is not None


def start_emulators():
    """Start Firebase emulators."""
    firebase_dir = Path("firebase")

    if not firebase_dir.exists():
        print("Firebase directory not found. Creating it...")
        firebase_dir.mkdir(exist_ok=True)

    print("Starting Firebase emulators...")
    try:
        # Start emulators in the background
        process = subprocess.Popen(
            ["firebase", "emulators:start", "--project", "demo-project"],
            cwd="firebase",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        print("Firebase emulators starting...")
        print("Emulator UI will be available at: http://localhost:4000")
        print("Auth Emulator: http://localhost:9099")
        print("Firestore Emulator: http://localhost:8080")
        print("Storage Emulator: http://localhost:9199")
        print("\nPress Ctrl+C to stop emulators")

        # Wait for the process
        process.wait()

    except KeyboardInterrupt:
        print("\nStopping Firebase emulators...")
        process.terminate()
        process.wait()
        print("Firebase emulators stopped")
    except Exception as e:
        print(f"Error starting emulators: {e}")


def stop_emulators():
    """Stop Firebase emulators."""
    print("Stopping Firebase emulators...")
    result = run_command(["firebase", "emulators:stop"], cwd="firebase", check=False)
    if result is not None:
        print("Firebase emulators stopped")
    else:
        print("No running emulators found or failed to stop")


def export_emulator_data(output_dir: str = "emulator-data"):
    """Export emulator data."""
    firebase_dir = Path("firebase")
    export_path = firebase_dir / output_dir

    print(f"Exporting emulator data to {export_path}...")

    # Create export directory
    export_path.mkdir(exist_ok=True, parents=True)

    result = run_command(
        ["firebase", "emulators:export", str(export_path), "--project", "demo-project"],
        cwd="firebase",
    )

    if result is not None:
        print(f"✅ Emulator data exported to {export_path}")
    else:
        print("❌ Failed to export emulator data")


def import_emulator_data(import_dir: str = "emulator-data"):
    """Start emulators with imported data."""
    firebase_dir = Path("firebase")
    import_path = firebase_dir / import_dir

    if not import_path.exists():
        print(f"Import directory {import_path} not found")
        return

    print(f"Starting emulators with data from {import_path}...")

    try:
        process = subprocess.Popen(
            [
                "firebase",
                "emulators:start",
                "--import",
                str(import_path),
                "--project",
                "demo-project",
            ],
            cwd="firebase",
        )

        print("Press Ctrl+C to stop emulators")
        process.wait()

    except KeyboardInterrupt:
        print("\nStopping Firebase emulators...")
        process.terminate()
        process.wait()


def clear_emulator_data():
    """Clear emulator data."""
    firebase_dir = Path("firebase")
    data_dirs = [
        "emulators/auth_export",
        "emulators/firestore_export",
        "emulators/storage_export",
    ]

    print("Clearing emulator data...")

    import shutil

    for data_dir in data_dirs:
        full_path = firebase_dir / data_dir
        if full_path.exists():
            shutil.rmtree(full_path)
            print(f"Cleared {full_path}")

    print("✅ Emulator data cleared")


def setup_firebase_project():
    """Initialize Firebase project."""
    firebase_dir = Path("firebase")
    firebase_json = firebase_dir / "firebase.json"

    if firebase_json.exists():
        print("Firebase project already configured")
        return

    print("Setting up Firebase project...")

    # Create basic firebase.json if it doesn't exist
    if not firebase_json.exists():
        config = {
            "firestore": {
                "rules": "firestore.rules",
                "indexes": "firestore.indexes.json",
            },
            "storage": {"rules": "storage.rules"},
            "emulators": {
                "auth": {"port": 9099},
                "firestore": {"port": 8080},
                "storage": {"port": 9199},
                "ui": {"enabled": True, "port": 4000},
            },
        }

        with open(firebase_json, "w") as f:
            json.dump(config, f, indent=2)

        print(f"Created {firebase_json}")

    # Set demo project
    result = run_command(
        ["firebase", "use", "--add", "demo-project"], cwd="firebase", check=False
    )

    print("✅ Firebase project setup complete")


def show_status():
    """Show Firebase emulator status."""
    try:
        import requests

        services = {
            "Emulator UI": "http://localhost:4000",
            "Auth Emulator": "http://localhost:9099",
            "Firestore Emulator": "http://localhost:8080",
            "Storage Emulator": "http://localhost:9199",
        }

        print("Firebase Emulator Status:")
        print("-" * 30)

        for name, url in services.items():
            try:
                response = requests.get(url, timeout=2)
                status = "🟢 Running" if response.status_code == 200 else "🟡 Issues"
            except:
                status = "🔴 Stopped"

            print(f"{name}: {status}")

    except ImportError:
        print(
            "Install 'requests' package to check emulator status: pip install requests"
        )


def main():
    """Main Firebase management function."""
    if len(sys.argv) < 2:
        print("Firebase Emulator Management")
        print("Usage: python scripts/firebase.py <command>")
        print("\nCommands:")
        print("  start          Start Firebase emulators")
        print("  stop           Stop Firebase emulators")
        print("  restart        Restart Firebase emulators")
        print("  status         Show emulator status")
        print("  export [dir]   Export emulator data")
        print("  import [dir]   Import emulator data and start")
        print("  clear          Clear emulator data")
        print("  setup          Setup Firebase project")
        print("  install        Install Firebase CLI")
        return 1

    command = sys.argv[1]

    # Check Firebase CLI installation for most commands
    if command not in ["install", "setup"] and not check_firebase_cli():
        print("Firebase CLI not found. Install it with:")
        print("  python scripts/firebase.py install")
        print("  OR: npm install -g firebase-tools")
        return 1

    if command == "start":
        start_emulators()
    elif command == "stop":
        stop_emulators()
    elif command == "restart":
        stop_emulators()
        time.sleep(2)
        start_emulators()
    elif command == "status":
        show_status()
    elif command == "export":
        export_dir = sys.argv[2] if len(sys.argv) > 2 else "emulator-data"
        export_emulator_data(export_dir)
    elif command == "import":
        import_dir = sys.argv[2] if len(sys.argv) > 2 else "emulator-data"
        import_emulator_data(import_dir)
    elif command == "clear":
        clear_emulator_data()
    elif command == "setup":
        if not check_firebase_cli():
            print("Firebase CLI not found. Installing...")
            if not install_firebase_cli():
                print("Failed to install Firebase CLI")
                return 1
        setup_firebase_project()
    elif command == "install":
        if not install_firebase_cli():
            return 1
        print("✅ Firebase CLI installed successfully")
    else:
        print(f"Unknown command: {command}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

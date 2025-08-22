#!/usr/bin/env python3
"""
Test runner script with Firebase emulator support.
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def run_command(command: list, cwd: str = None, env: dict = None, check: bool = True):
    """Run a command with proper error handling."""
    try:
        if env:
            env_vars = os.environ.copy()
            env_vars.update(env)
        else:
            env_vars = os.environ

        result = subprocess.run(command, cwd=cwd, env=env_vars, check=check, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"Command not found: {command[0]}")
        return False


def check_firebase_emulators():
    """Check if Firebase emulators are running."""
    try:
        import requests

        response = requests.get("http://localhost:4000", timeout=2)
        return response.status_code == 200
    except:
        return False


def start_firebase_emulators_for_tests():
    """Start Firebase emulators for testing."""
    print("Starting Firebase emulators for tests...")

    # Check if emulators are already running
    if check_firebase_emulators():
        print("✅ Firebase emulators are already running")
        return True

    firebase_dir = Path("firebase")
    if not firebase_dir.exists():
        print("Firebase directory not found.")
        return False

    try:
        # Start emulators in background
        process = subprocess.Popen(
            [
                "firebase",
                "emulators:start",
                "--project",
                "demo-project",
                "--only",
                "auth,firestore,storage",
            ],
            cwd="firebase",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        # Wait for emulators to start
        print("Waiting for Firebase emulators to start...")
        for i in range(30):  # Wait up to 30 seconds
            if check_firebase_emulators():
                print("✅ Firebase emulators started successfully")
                return True
            time.sleep(1)
            if i % 5 == 0:
                print(f"Still waiting... ({i + 1}/30 seconds)")

        print("❌ Firebase emulators failed to start within 30 seconds")
        process.terminate()
        return False

    except Exception as e:
        print(f"Error starting Firebase emulators: {e}")
        return False


def run_tests(test_args: list = None):
    """Run tests with pytest."""
    print("Running tests...")

    # Set test environment variables
    test_env = {
        "ENVIRONMENT": "test",
        "FIREBASE_PROJECT_ID": "demo-project",
        "USE_FIREBASE_EMULATOR": "true",
        "FIREBASE_AUTH_EMULATOR_HOST": "localhost:9099",
        "FIRESTORE_EMULATOR_HOST": "localhost:8080",
        "FIREBASE_STORAGE_EMULATOR_HOST": "localhost:9199",
        "SECRET_KEY": "test-secret-key-not-for-production",
        "LOG_LEVEL": "WARNING",
        "LOG_FORMAT": "console",
    }

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    if test_args:
        cmd.extend(test_args)
    else:
        # Default test arguments
        cmd.extend(
            ["tests/", "-v", "--tb=short", "--strict-markers", "--disable-warnings"]
        )

    # Add coverage if requested
    if "--cov" not in cmd and "--no-cov" not in (test_args or []):
        cmd.extend(
            ["--cov=app", "--cov-report=term-missing", "--cov-report=html:htmlcov"]
        )

    print(f"Running: {' '.join(cmd)}")
    return run_command(cmd, env=test_env)


def run_linting():
    """Run code linting."""
    print("Running linting...")

    # Run ruff
    print("Running ruff...")
    if not run_command(["python", "-m", "ruff", "check", "app", "tests"]):
        return False

    # Run mypy
    print("Running mypy...")
    if not run_command(["python", "-m", "mypy", "app"], check=False):
        print("⚠️  MyPy found issues (non-blocking)")

    return True


def run_formatting_check():
    """Check code formatting."""
    print("Checking code formatting...")

    # Check with ruff format
    if not run_command(["python", "-m", "ruff", "format", "--check", "app", "tests"]):
        print(
            "❌ Code formatting issues found. Run 'uv run ruff format app tests' to fix."
        )
        return False

    print("✅ Code formatting is correct")
    return True


def main():
    """Main test runner function."""
    print("🧪 FastAPI CloudRun Kit Test Runner")
    print("=" * 50)

    # Parse arguments
    skip_emulators = "--no-firebase" in sys.argv
    skip_lint = "--no-lint" in sys.argv
    skip_format = "--no-format" in sys.argv
    lint_only = "--lint-only" in sys.argv
    format_only = "--format-only" in sys.argv

    # Remove our custom arguments
    test_args = [
        arg
        for arg in sys.argv[1:]
        if not arg.startswith("--no-") and arg not in ["--lint-only", "--format-only"]
    ]

    success = True

    try:
        # Format check only
        if format_only:
            return 0 if run_formatting_check() else 1

        # Lint only
        if lint_only:
            return 0 if run_linting() else 1

        # Start Firebase emulators if needed
        if not skip_emulators:
            if not start_firebase_emulators_for_tests():
                print("❌ Failed to start Firebase emulators")
                if "--firebase-required" in sys.argv:
                    return 1
                else:
                    print(
                        "⚠️  Continuing without Firebase emulators (some tests may fail)"
                    )

        # Run formatting check
        if not skip_format:
            if not run_formatting_check():
                success = False

        # Run linting
        if not skip_lint:
            if not run_linting():
                success = False

        # Run tests
        if not run_tests(test_args):
            success = False

        # Summary
        print("\n" + "=" * 50)
        if success:
            print("🎉 All checks passed!")
        else:
            print("❌ Some checks failed!")

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        return 1


def show_help():
    """Show help message."""
    print("""
FastAPI CloudRun Kit Test Runner

Usage: python scripts/test.py [OPTIONS] [PYTEST_ARGS]

OPTIONS:
    --no-firebase       Skip starting Firebase emulators
    --no-lint          Skip linting checks
    --no-format        Skip formatting checks
    --lint-only        Only run linting (skip tests)
    --format-only      Only check formatting (skip tests)
    --firebase-required Exit if Firebase emulators fail to start

PYTEST_ARGS:
    Any additional arguments will be passed to pytest

EXAMPLES:
    python scripts/test.py                    # Run all checks and tests
    python scripts/test.py --no-lint         # Skip linting
    python scripts/test.py tests/test_auth.py # Run specific test file
    python scripts/test.py --lint-only       # Only run linting
    python scripts/test.py -v -s             # Verbose and no capture
    python scripts/test.py --cov=app         # Run with coverage
    python scripts/test.py -k test_auth      # Run tests matching pattern

MARKERS:
    pytest -m "not slow"                     # Skip slow tests
    pytest -m "firebase"                     # Only Firebase tests
    pytest -m "unit"                         # Only unit tests
    pytest -m "integration"                  # Only integration tests

ENVIRONMENT:
    Tests automatically use Firebase emulators and test configuration.
    Set PYTEST_ARGS environment variable for default arguments.
""")


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        show_help()
        sys.exit(0)

    exit_code = main()
    sys.exit(exit_code)

"""
Verification script to test multi-app architecture
"""

import subprocess
import sys


def check_imports():
    """Check if all required packages are installed"""
    print("Checking Python packages...")
    try:
        import flask

        print(f"  Flask {flask.__version__}")
    except ImportError:
        print("  Flask not installed")
        return False

    try:
        import flask_sqlalchemy  # noqa: F401

        print("  Flask-SQLAlchemy installed")
    except ImportError:
        print("  Flask-SQLAlchemy not installed")
        return False

    try:
        import requests

        print(f"  requests {requests.__version__}")
    except ImportError:
        print("  requests not installed (needed for local_proxy.py)")
        return False

    print("  Note: bjoern will be used in production Docker only")
    return True


def check_files():
    """Check if all required files exist"""
    import os

    print("\nChecking files...")

    files = [
        "app_factory.py",
        "run_bjoern.py",
        "local_proxy.py",
        "start_local.py",
        "nginx.conf",
        "supervisord.conf",
        "Dockerfile",
        "routes_read.py",
        "routes_write.py",
        "routes_operations.py",
        "database.py",
    ]

    all_exist = True
    for f in files:
        if os.path.exists(f):
            print(f"  {f}")
        else:
            print(f"  {f} (missing)")
            all_exist = False

    return all_exist


def test_app_creation():
    """Test if apps can be created"""
    print("\nTesting app creation...")

    apps = ["read", "write", "operations"]

    for app_type in apps:
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    f'from app_factory import create_app; app = create_app("{app_type}"); print("OK")',
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if "OK" in result.stdout or "OK" in result.stderr:
                print(f"  {app_type} app created successfully")
            else:
                print(f"  {app_type} app creation failed")
                print(f"    Error: {result.stderr[:200]}")
        except Exception as e:
            print(f"  {app_type} test failed: {str(e)[:100]}")


if __name__ == "__main__":
    print("MULTI-APP ARCHITECTURE VERIFICATION")
    print("-" * 40)

    imports_ok = check_imports()
    files_ok = check_files()

    if imports_ok and files_ok:
        test_app_creation()

    print("\n" + "-" * 40)
    if imports_ok and files_ok:
        print("Verification complete")
        print("\nNext steps:")
        print("1. Start local development: python start_local.py")
        print("2. Or build production: docker-compose up --build")
    else:
        print("Verification failed - fix issues above")
    print("-" * 40)

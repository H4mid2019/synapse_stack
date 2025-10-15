"""
Test the text extractor independently
"""

import requests

EXTRACTOR_URL = "http://localhost:6004"


def test_extractor_health():
    """Test if extractor is running"""
    try:
        response = requests.get(f"{EXTRACTOR_URL}/health", timeout=5)
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False


def test_extract_job():
    """Test adding a job to extraction queue"""
    try:
        # Test with a fake file ID (should fail gracefully)
        data = {"file_id": 999, "file_path": "fake_path"}
        response = requests.post(f"{EXTRACTOR_URL}/extract", json=data, timeout=5)
        print(f"Extract job: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code in [200, 404]  # 404 is OK for fake file
    except Exception as e:
        print(f"Extract job failed: {e}")
        return False


def test_extraction_status():
    """Test getting extraction status"""
    try:
        # Test with a fake file ID
        response = requests.get(f"{EXTRACTOR_URL}/status/999", timeout=5)
        print(f"Status check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code in [200, 404]  # Both OK
    except Exception as e:
        print(f"Status check failed: {e}")
        return False


def main():
    print("Testing Text Extractor Service")
    print("=" * 40)

    # Test 1: Health check
    print("\n1. Health Check:")
    if not test_extractor_health():
        print("❌ Extractor is not running or not responding")
        return

    print("✅ Extractor is running")

    # Test 2: Extract job
    print("\n2. Extract Job Test:")
    if test_extract_job():
        print("✅ Extract endpoint working")
    else:
        print("❌ Extract endpoint failed")

    # Test 3: Status check
    print("\n3. Status Check Test:")
    if test_extraction_status():
        print("✅ Status endpoint working")
    else:
        print("❌ Status endpoint failed")

    print("\n" + "=" * 40)
    print("Test completed!")


if __name__ == "__main__":
    main()

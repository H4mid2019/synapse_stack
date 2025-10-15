"""
Test script for text extractor standalone testing
"""

import json

import requests

EXTRACTOR_URL = "http://localhost:6004"


def test_list_files():
    """List all files available for testing"""
    print("\n📁 Available Files for Testing:")
    print("=" * 50)

    try:
        response = requests.get(f"{EXTRACTOR_URL}/test/files")
        data = response.json()

        if response.status_code == 200:
            print(f"Storage Type: {data['storage_type']}")
            if data.get("gcs_bucket"):
                print(f"GCS Bucket: {data['gcs_bucket']}")
            print(f"Total Files: {data['total_files']}\n")

            for file_info in data["files"]:
                status = "✅" if file_info["file_exists"] else "❌"
                extracted = "✅" if file_info["content_extracted"] else "❌"

                print(f"{status} File ID: {file_info['id']}")
                print(f"   Name: {file_info['name']}")
                print(f"   Type: {file_info['mime_type']}")
                print(f"   Size: {file_info['size']} bytes")
                print(f"   Extracted: {extracted}")
                print(f"   Path: {file_info['file_path']}")

                if file_info["extraction_error"]:
                    print(f"   ❌ Error: {file_info['extraction_error']}")
                print()

            return data["files"]
        else:
            print(f"❌ Error: {data}")
            return []

    except Exception as e:
        print(f"❌ Connection error: {e}")
        return []


def test_extract_file(file_id):
    """Test extraction for a specific file"""
    print(f"\n🔬 Testing Extraction for File ID: {file_id}")
    print("=" * 50)

    try:
        response = requests.post(f"{EXTRACTOR_URL}/test/extract/{file_id}")
        data = response.json()

        if response.status_code == 200:
            print("✅ Extraction Test SUCCESSFUL!")
            print(f"File: {data['file_name']}")
            print(f"Storage: {data['storage_type']}")
            print(f"Content Size: {data['content_length']} bytes")
            print(f"Extracted Text: {data['extracted_text_length']} characters")
            print(f"Preview: {data['extracted_preview']}")
        else:
            print("❌ Extraction Test FAILED!")
            print(f"Error: {data['error']}")
            if "details" in data:
                print(f"Details: {data['details']}")
            if "file_path" in data:
                print(f"File Path: {data['file_path']}")

    except Exception as e:
        print(f"❌ Connection error: {e}")


def get_file_status(file_id):
    """Get detailed status of a file"""
    print(f"\n📊 File Status for ID: {file_id}")
    print("=" * 50)

    try:
        response = requests.get(f"{EXTRACTOR_URL}/status/{file_id}")
        data = response.json()

        if response.status_code == 200:
            print(f"File: {data['file_name']}")
            print(f"Path: {data['file_path']}")
            print(f"Type: {data['mime_type']}")
            print(f"Size: {data['size']} bytes")
            print(f"Extracted: {'✅' if data['content_extracted'] else '❌'}")
            print(f"Has Content: {'✅' if data['has_content'] else '❌'}")

            if data["extraction_error"]:
                print(f"❌ Error: {data['extraction_error']}")
        else:
            print(f"❌ Error: {data}")

    except Exception as e:
        print(f"❌ Connection error: {e}")


def main():
    """Main test function"""
    print("🧪 Text Extractor Standalone Test")
    print("=" * 60)

    # Test health first
    try:
        response = requests.get(f"{EXTRACTOR_URL}/health")
        if response.status_code == 200:
            print("✅ Extractor is healthy and running")
        else:
            print("❌ Extractor health check failed")
            return
    except:
        print("❌ Cannot connect to extractor - make sure it's running on port 6004")
        return

    # List available files
    files = test_list_files()

    if not files:
        print("No files found for testing. Upload some PDF files first.")
        return

    # Test extraction for each file
    for file_info in files:
        file_id = file_info["id"]

        # Get current status
        get_file_status(file_id)

        # Test extraction if file exists
        if file_info["file_exists"]:
            test_extract_file(file_id)
        else:
            print(f"⚠️  Skipping file {file_id} - file not found in storage")

        print("-" * 50)


if __name__ == "__main__":
    main()

# backend/test_endpoints.py
"""
End-to-end test for the Iris Recognition Emergency System.
Uses sample images from sample_data/ to test register, scan, admin endpoints.
"""

import os
import sys
import json
import requests
import time

BASE_URL = "http://127.0.0.1:5000/api"
SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_data")

# Assign sample images to test "persons"
# Using different images to simulate different people and re-scans
TEST_PERSONS = [
    {
        "name": "Rahul Kumar",
        "address": "42 MG Road, Bangalore, Karnataka",
        "phone_no": "+91-9876543210",
        "relationship": "Father - Suresh Kumar (+91-9876543200)",
        "image": "PXL_20260224_104204925.jpg.jpeg",
    },
    {
        "name": "Priya Sharma",
        "address": "15 Nehru Street, Chennai, Tamil Nadu",
        "phone_no": "+91-9123456789",
        "relationship": "Mother - Anita Sharma (+91-9123456700)",
        "image": "PXL_20260224_104322019.jpg.jpeg",
    },
    {
        "name": "Amit Patel",
        "address": "88 SG Highway, Ahmedabad, Gujarat",
        "phone_no": "+91-9988776655",
        "relationship": "Wife - Neha Patel (+91-9988776600)",
        "image": "PXL_20260224_104359852.MP.jpg.jpeg",
    },
]

# Images to use for scan/matching tests
SCAN_IMAGES = [
    "PXL_20260224_104206983.jpg.jpeg",   # similar to person 1
    "PXL_20260224_104209396.jpg.jpeg",   # another angle
    "PXL_20260224_104322805.jpg.jpeg",   # similar to person 2
    "PXL_20260224_104401552.jpg.jpeg",   # another test
    "PXL_20260224_104407973.jpg.jpeg",   # another test
]

PASS = "\033[92m PASS \033[0m"
FAIL = "\033[91m FAIL \033[0m"
WARN = "\033[93m WARN \033[0m"

registered_ids = []


def separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_health():
    """Test the health check endpoint."""
    separator("1. Health Check")
    try:
        r = requests.get("http://127.0.0.1:5000/")
        data = r.json()
        if data.get("status") == "running":
            print(f"  [{PASS}] Server is running: {data}")
            return True
        else:
            print(f"  [{FAIL}] Unexpected response: {data}")
            return False
    except Exception as e:
        print(f"  [{FAIL}] Cannot connect to server: {e}")
        return False


def test_register_upload(person):
    """Register a person using image upload endpoint."""
    image_path = os.path.join(SAMPLE_DIR, person["image"])

    if not os.path.exists(image_path):
        print(f"  [{FAIL}] Image not found: {image_path}")
        return None

    with open(image_path, "rb") as img:
        files = {"image": (person["image"], img, "image/jpeg")}
        data = {
            "name": person["name"],
            "address": person["address"],
            "phone_no": person["phone_no"],
            "relationship": person["relationship"],
        }

        try:
            r = requests.post(f"{BASE_URL}/register/upload", data=data, files=files)
            result = r.json()

            if r.status_code in (200, 201) and result.get("status") == "Success":
                user_id = result.get("user_id")
                print(f"  [{PASS}] Registered '{person['name']}' -> ID: {user_id}")
                return user_id
            else:
                print(f"  [{WARN}] Register response ({r.status_code}): {result.get('message', result)}")
                return None
        except Exception as e:
            print(f"  [{FAIL}] Register error for '{person['name']}': {e}")
            return None


def test_scan_upload(image_name):
    """Scan an image using the upload endpoint."""
    image_path = os.path.join(SAMPLE_DIR, image_name)

    if not os.path.exists(image_path):
        print(f"  [{FAIL}] Image not found: {image_path}")
        return None

    with open(image_path, "rb") as img:
        files = {"image": (image_name, img, "image/jpeg")}

        try:
            r = requests.post(f"{BASE_URL}/scan/upload", files=files)
            result = r.json()

            status = result.get("status", "Unknown")
            if status == "Match Found":
                data = result.get("data", {})
                confidence = result.get("confidence_score", 0)
                hamming = result.get("hamming_distance", "N/A")
                print(f"  [{PASS}] MATCH: {data.get('name')} | Confidence: {confidence}% | Hamming: {hamming}")
            elif status == "No Match Found":
                print(f"  [{WARN}] No match found for {image_name}")
            else:
                print(f"  [{WARN}] Scan response ({r.status_code}): {result.get('message', result)}")

            return result
        except Exception as e:
            print(f"  [{FAIL}] Scan error for {image_name}: {e}")
            return None


def test_get_all_users():
    """Test admin: get all users."""
    try:
        r = requests.get(f"{BASE_URL}/users")
        result = r.json()
        total = result.get("total_users", 0)
        users = result.get("data", [])
        print(f"  [{PASS}] Total users in DB: {total}")
        for u in users:
            print(f"       - {u.get('name')} | {u.get('phone_no')} | {u.get('relationship')}")
        return result
    except Exception as e:
        print(f"  [{FAIL}] Get users error: {e}")
        return None


def test_get_user_by_id(user_id):
    """Test admin: get single user."""
    try:
        r = requests.get(f"{BASE_URL}/users/{user_id}")
        result = r.json()
        if result.get("status") == "Success":
            data = result.get("data", {})
            print(f"  [{PASS}] User found: {data.get('name')}")
        else:
            print(f"  [{WARN}] User not found: {result}")
        return result
    except Exception as e:
        print(f"  [{FAIL}] Get user error: {e}")
        return None


def test_stats():
    """Test admin: stats endpoint."""
    try:
        r = requests.get(f"{BASE_URL}/stats")
        result = r.json()
        print(f"  [{PASS}] Stats: {result}")
        return result
    except Exception as e:
        print(f"  [{FAIL}] Stats error: {e}")
        return None


def test_duplicate_registration(person):
    """Try registering the same image again — should be rejected."""
    image_path = os.path.join(SAMPLE_DIR, person["image"])

    with open(image_path, "rb") as img:
        files = {"image": (person["image"], img, "image/jpeg")}
        data = {
            "name": person["name"],
            "address": person["address"],
            "phone_no": person["phone_no"],
            "relationship": person["relationship"],
        }

        try:
            r = requests.post(f"{BASE_URL}/register/upload", data=data, files=files)
            result = r.json()

            if r.status_code == 409:
                print(f"  [{PASS}] Duplicate correctly rejected: {result.get('message')}")
            elif result.get("status") == "Error":
                print(f"  [{WARN}] Rejected but with status {r.status_code}: {result.get('message')}")
            else:
                print(f"  [{FAIL}] Duplicate was NOT rejected: {result}")
            return result
        except Exception as e:
            print(f"  [{FAIL}] Duplicate test error: {e}")
            return None


def test_delete_user(user_id):
    """Test deleting a user."""
    try:
        r = requests.delete(f"{BASE_URL}/users/{user_id}")
        result = r.json()
        if result.get("status") == "Success":
            print(f"  [{PASS}] Deleted user {user_id}")
        else:
            print(f"  [{WARN}] Delete response: {result}")
        return result
    except Exception as e:
        print(f"  [{FAIL}] Delete error: {e}")
        return None


def main():
    print("\n" + "=" * 60)
    print("  IRIS RECOGNITION EMERGENCY SYSTEM — FULL TEST SUITE")
    print("=" * 60)

    # ---- 1. Health Check ----
    if not test_health():
        print("\n  Server not reachable. Please start with: python app.py")
        sys.exit(1)

    # ---- 2. Register Users ----
    separator("2. Registration (Upload Endpoint)")
    for person in TEST_PERSONS:
        uid = test_register_upload(person)
        if uid:
            registered_ids.append(uid)

    # ---- 3. Duplicate Check ----
    separator("3. Duplicate Registration Test")
    if TEST_PERSONS:
        test_duplicate_registration(TEST_PERSONS[0])

    # ---- 4. Scan / Match ----
    separator("4. Scan & Match (Upload Endpoint)")
    for img in SCAN_IMAGES:
        test_scan_upload(img)

    # ---- 5. Admin: List Users ----
    separator("5. Admin — List All Users")
    test_get_all_users()

    # ---- 6. Admin: Get User By ID ----
    separator("6. Admin — Get User By ID")
    if registered_ids:
        test_get_user_by_id(registered_ids[0])

    # ---- 7. Admin: Stats ----
    separator("7. Admin — System Stats")
    test_stats()

    # ---- 8. Admin: Delete User ----
    separator("8. Admin — Delete User")
    if registered_ids:
        test_delete_user(registered_ids[-1])

    # ---- 9. Final Count ----
    separator("9. Final Stats After Deletion")
    test_stats()

    print(f"\n{'='*60}")
    print("  TEST SUITE COMPLETE")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

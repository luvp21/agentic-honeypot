import urllib.request
import urllib.error
import json
import sys
import time

API_URL = "http://localhost:8000"
API_KEY = "honeypot-secret-key-123"

def print_result(test_name, success, details=""):
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} - {test_name}")
    if details:
        print(f"   Details: {details}")

def test_connectivity():
    try:
        with urllib.request.urlopen(f"{API_URL}/") as response:
            if response.status == 200:
                print_result("Connectivity Check", True, "Server is reachable")
                return True
    except urllib.error.URLError:
        print_result("Connectivity Check", False, "Connection refused. Is the server running?")
        return False
    except Exception as e:
        print_result("Connectivity Check", False, str(e))
        return False

def test_authentication_missing():
    try:
        req = urllib.request.Request(f"{API_URL}/api/simulate/scam", method="POST")
        urllib.request.urlopen(req)
        print_result("Auth Missing Check", False, "Expected 403, got 200 OK")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print_result("Auth Missing Check", True, "Resource forbidden as expected")
        else:
            print_result("Auth Missing Check", False, f"Expected 403, got {e.code}")
    except Exception as e:
        print_result("Auth Missing Check", False, str(e))

def test_authentication_invalid():
    try:
        req = urllib.request.Request(f"{API_URL}/api/simulate/scam", method="POST")
        req.add_header("X-API-Key", "invalid-key")
        urllib.request.urlopen(req)
        print_result("Auth Invalid Check", False, "Expected 403, got 200 OK")
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print_result("Auth Invalid Check", True, "Resource forbidden as expected")
        else:
            print_result("Auth Invalid Check", False, f"Expected 403, got {e.code}")
    except Exception as e:
        print_result("Auth Invalid Check", False, str(e))

def test_valid_request():
    try:
        req = urllib.request.Request(f"{API_URL}/api/simulate/scam?scam_type=phishing", method="POST")
        req.add_header("X-API-Key", API_KEY)
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                if data.get("full_conversation", {}).get("is_scam") is True and "conversation_log" in data:
                    print_result("Valid Request Check", True, "Simulation successful")
                else:
                    print_result("Valid Request Check", False, "Invalid response structure")
            else:
                print_result("Valid Request Check", False, f"Status {response.status}")
    except Exception as e:
        print_result("Valid Request Check", False, str(e))

def main():
    print("Running Honeypot API Verification...\n")
    if not test_connectivity():
        sys.exit(1)

    test_authentication_missing()
    test_authentication_invalid()
    test_valid_request()

if __name__ == "__main__":
    main()

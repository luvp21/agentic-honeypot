
import urllib.request
import json
import ssl

def test_api():
    url = "https://agentic-honeypot-laju.onrender.com/api/conversation/message"
    api_key = "honeypot-secret-key-123"

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }

    data = {
        "message": "Hello, I received a message about a refund. Can you help me?",
        "conversation_id": None
    }

    json_data = json.dumps(data).encode('utf-8')

    req = urllib.request.Request(url, data=json_data, headers=headers, method='POST')

    # Create a context that doesn't verify SSL certificates (just in case, though Render usually has valid SSL)
    # Using default context is better if SSL is valid.
    ctx = ssl.create_default_context()

    print(f"Sending request to {url}...")
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            status_code = response.getcode()
            response_body = response.read().decode('utf-8')

            print(f"Status Code: {status_code}")
            print("Response Headers:")
            print(response.info())
            print("Response Body:")
            try:
                parsed_json = json.loads(response_body)
                print(json.dumps(parsed_json, indent=2))
            except json.JSONDecodeError:
                print(response_body)

    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code}")
        print(e.read().decode('utf-8'))
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_api()

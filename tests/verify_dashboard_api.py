import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://localhost:8080"

def test_get_endpoints():
    endpoints = [
        "/",
        "/api/status",
        "/api/benchmark",
        "/api/hex_sample?type=cipher",
        "/api/recent_events"
    ]
    print("=== Testing GET Endpoints ===")
    all_ok = True
    for ep in endpoints:
        url = f"{BASE_URL}{ep}"
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                body = resp.read()
                print(f"[PASS] GET {ep} -> HTTP {status} (Bytes: {len(body)})")
                if status != 200:
                    all_ok = False
        except Exception as e:
            print(f"[FAIL] GET {ep} -> {e}")
            all_ok = False
    return all_ok

def test_post_actions():
    actions = [
        "simulate_entropy",
        "simulate_canary",
        "simulate_encryptor",
        "simulate_benign"
    ]
    print("\n=== Testing POST /api/action Simulation Payloads ===")
    all_ok = True
    for action in actions:
        url = f"{BASE_URL}/api/action"
        payload = json.dumps({"action": action}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req) as resp:
                status = resp.status
                body = json.loads(resp.read().decode("utf-8"))
                print(f"[PASS] POST action '{action}' -> HTTP {status} (Resp: {body})")
                if status != 200 or not body.get("success"):
                    all_ok = False
        except Exception as e:
            print(f"[FAIL] POST action '{action}' -> {e}")
            all_ok = False
        time.sleep(1)
    return all_ok

def test_sse_stream():
    print("\n=== Testing SSE Stream (/api/events) ===")
    url = f"{BASE_URL}/api/events"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as resp:
            # Read first line
            first_line = resp.readline().decode("utf-8").strip()
            print(f"Received SSE line: {first_line}")
            if "HANDSHAKE" in first_line:
                print("[PASS] SSE Handshake confirmed successfully!")
                return True
            else:
                print(f"[FAIL] Expected HANDSHAKE in line, got: {first_line}")
                return False
    except Exception as e:
        print(f"[FAIL] SSE stream failed: {e}")
        return False

if __name__ == "__main__":
    r1 = test_get_endpoints()
    r2 = test_post_actions()
    r3 = test_sse_stream()
    if r1 and r2 and r3:
        print("\n[+] All Dashboard & API Endpoint Tests PASSED!")
        exit(0)
    else:
        print("\n[-] Some Dashboard / API Endpoint Tests FAILED!")
        exit(1)

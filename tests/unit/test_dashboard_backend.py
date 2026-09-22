#!/usr/bin/env python3
"""
Unit and Integration Test Suite for Project Aegis Dashboard Backend (server.py)
Tests all REST endpoints, SSE handshake, simulation actions, and error handling.
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error
import threading
import subprocess

PORT = 8899
BASE_URL = f"http://127.0.0.1:{PORT}"

def run_tests():
    server_proc = subprocess.Popen(
        [sys.executable, "dashboard/server.py", str(PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(1.2)

    try:
        print(f"[*] Testing Dashboard Backend on {BASE_URL}...")
        
        # 1. GET /
        req = urllib.request.urlopen(f"{BASE_URL}/")
        assert req.status == 200
        content = req.read().decode("utf-8")
        assert "<title>Project Aegis" in content
        print("[PASS] GET / (Dashboard HTML served)")

        # 2. GET /design_system.css
        req = urllib.request.urlopen(f"{BASE_URL}/design_system.css")
        assert req.status == 200
        css = req.read().decode("utf-8")
        assert "--color-bg" in css
        print("[PASS] GET /design_system.css (CSS design system served)")

        # 3. GET /api/status
        req = urllib.request.urlopen(f"{BASE_URL}/api/status")
        assert req.status == 200
        status_data = json.loads(req.read().decode("utf-8"))
        assert "running" in status_data
        assert "mode" in status_data
        assert "canaries_count" in status_data
        print(f"[PASS] GET /api/status (Running: {status_data['running']}, Mode: {status_data['mode']})")

        # 4. GET /api/benchmark
        req = urllib.request.urlopen(f"{BASE_URL}/api/benchmark")
        assert req.status == 200
        bench = json.loads(req.read().decode("utf-8"))
        assert "aegis" in bench
        assert "crowdstrike_edr" in bench
        assert bench["aegis"]["latency_us"] == 2.4
        print("[PASS] GET /api/benchmark (Architectural benchmark verified)")

        # 5. GET /api/hex_sample
        req_cipher = urllib.request.urlopen(f"{BASE_URL}/api/hex_sample?type=cipher")
        cipher_data = json.loads(req_cipher.read().decode("utf-8"))
        assert cipher_data["type"] == "cipher"
        assert len(cipher_data["hex"]) == 256 # 128 bytes = 256 hex chars
        
        req_plain = urllib.request.urlopen(f"{BASE_URL}/api/hex_sample?type=plain")
        plain_data = json.loads(req_plain.read().decode("utf-8"))
        assert plain_data["type"] == "plain"
        assert len(plain_data["hex"]) == 256
        print("[PASS] GET /api/hex_sample (Cipher and plaintext hex streams verified)")

        # 6. GET /api/recent_events
        req = urllib.request.urlopen(f"{BASE_URL}/api/recent_events")
        assert req.status == 200
        recent = json.loads(req.read().decode("utf-8"))
        assert "events" in recent
        assert isinstance(recent["events"], list)
        print(f"[PASS] GET /api/recent_events ({len(recent['events'])} events retrieved)")

        # 7. SSE /api/events handshake
        req = urllib.request.Request(f"{BASE_URL}/api/events")
        sse_resp = urllib.request.urlopen(req, timeout=5)
        line1 = sse_resp.readline().decode("utf-8")
        assert "data: {" in line1
        assert "HANDSHAKE" in line1
        print("[PASS] GET /api/events (SSE stream handshake verified)")
        sse_resp.close()

        # 8. POST /api/action Error Handling (Malformed JSON -> 400)
        try:
            req = urllib.request.Request(
                f"{BASE_URL}/api/action",
                data=b"invalid-json{not-json",
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req)
            assert False, "Should have returned 400"
        except urllib.error.HTTPError as he:
            assert he.code == 400
            print("[PASS] POST /api/action (Malformed JSON rejected with 400 Bad Request)")

        # 9. POST /api/action Error Handling (Unknown action -> 400)
        try:
            req = urllib.request.Request(
                f"{BASE_URL}/api/action",
                data=json.dumps({"action": "unknown_action_xyz"}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req)
            assert False, "Should have returned 400"
        except urllib.error.HTTPError as he:
            assert he.code == 400
            print("[PASS] POST /api/action (Unknown action rejected with 400 Bad Request)")

        # 10. POST /api/action simulate_entropy
        req = urllib.request.Request(
            f"{BASE_URL}/api/action",
            data=json.dumps({"action": "simulate_entropy"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        assert res["success"] is True
        print(f"[PASS] POST /api/action simulate_entropy: {res['message']}")

        # 11. POST /api/action simulate_canary
        req = urllib.request.Request(
            f"{BASE_URL}/api/action",
            data=json.dumps({"action": "simulate_canary"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        assert res["success"] is True
        print(f"[PASS] POST /api/action simulate_canary: {res['message']}")

        # 12. POST /api/action simulate_encryptor
        req = urllib.request.Request(
            f"{BASE_URL}/api/action",
            data=json.dumps({"action": "simulate_encryptor"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        assert res["success"] is True
        print(f"[PASS] POST /api/action simulate_encryptor: {res['message']}")

        # 13. POST /api/action simulate_benign
        req = urllib.request.Request(
            f"{BASE_URL}/api/action",
            data=json.dumps({"action": "simulate_benign"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        assert res["success"] is True
        print(f"[PASS] POST /api/action simulate_benign: {res['message']}")

        # 14. POST /api/action clear_logs
        req = urllib.request.Request(
            f"{BASE_URL}/api/action",
            data=json.dumps({"action": "clear_logs"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        res = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        assert res["success"] is True
        print(f"[PASS] POST /api/action clear_logs: {res['message']}")

        # 15. GET 404 Endpoint
        try:
            urllib.request.urlopen(f"{BASE_URL}/api/non_existent_route")
            assert False, "Should return 404"
        except urllib.error.HTTPError as he:
            assert he.code == 404
            print("[PASS] GET /api/non_existent_route (Returned 404 Not Found)")

        print("\n=== ALL 15 DASHBOARD BACKEND REST & SSE TESTS PASSED! ===")
    finally:
        server_proc.terminate()
        server_proc.wait()

if __name__ == "__main__":
    run_tests()

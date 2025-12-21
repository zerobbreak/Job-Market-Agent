import requests
import unittest
import json
import time

BASE_URL = "http://localhost:8000"

class APIHealthCheck(unittest.TestCase):
    
    def test_01_health(self):
        try:
            response = requests.get(f"{BASE_URL}/health")
            print(f"\nHealth Check: {response.status_code}")
            self.assertEqual(response.status_code, 200)
        except Exception as e:
            self.fail(f"Server not reachable: {e}")

    def test_02_endpoint_discovery(self):
        """Verify key endpoints respond (even if 401)"""
        endpoints = [
            ('/api/search-jobs', 'POST'),
            ('/api/profile/structured', 'GET'),
            ('/api/matches/last', 'GET')
        ]
        print("\nChecking Endpoints:")
        for path, method in endpoints:
            if method == 'GET':
                r = requests.get(f"{BASE_URL}{path}")
            else:
                r = requests.post(f"{BASE_URL}{path}")
            print(f"  {method} {path} -> {r.status_code}")
            # We expect 200, 401, or 400 (if missing body), but NOT 500 or 404
            self.assertIn(r.status_code, [200, 401, 400, 403, 429])
            self.assertNotEqual(r.status_code, 404, f"Endpoint {path} not found")
            self.assertNotEqual(r.status_code, 500, f"Endpoint {path} crashed")

if __name__ == "__main__":
    unittest.main()

import requests
import unittest

class TestAppLink(unittest.TestCase):
    def test_app_link_opens(self):
        url = "http://localhost:8501"
        try:
            response = requests.get(url, timeout=10)
            self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}")
            print("Link opens successfully!")
        except requests.exceptions.RequestException as e:
            self.fail(f"Failed to open link: {e}")

if __name__ == '__main__':
    unittest.main()
"""
Locust load test for itsmegram API
Tests concurrent user handling with queue system
"""

from locust import HttpUser, task, between
import random


class InstagramAnalyzerUser(HttpUser):
    """Simulates a user analyzing Instagram accounts"""

    wait_time = between(1, 5)

    def on_start(self):
        """Called when a user starts"""
        self.test_usernames = [
            "instagram",
            "natgeo",
            "nasa",
            "google",
            "apple",
            "microsoft",
            "amazon",
            "tesla",
            "spacex",
            "uber",
        ]

    @task(3)
    def analyze_profile(self):
        """Test analyze endpoint"""
        username = random.choice(self.test_usernames)

        with self.client.post(
            "/api/v1/analyze",
            json={"username": username},
            catch_response=True,
        ) as response:
            if response.status_code == 202:
                response.success()
            elif response.status_code == 503:
                # Server busy - expected under high load
                response.success()
            elif response.status_code == 429:
                # Rate limited - expected
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

    @task(1)
    def check_health(self):
        """Test health endpoint"""
        self.client.get("/api/v1/health")

    @task(2)
    def get_queue_status(self):
        """Test queue status endpoint"""
        self.client.get("/api/v1/queue/status")

    @task(1)
    def validate_username(self):
        """Test username validation"""
        username = random.choice(self.test_usernames)
        self.client.get(f"/api/v1/instagram/validate/{username}")


class BurstUser(HttpUser):
    """Simulates burst traffic"""

    wait_time = between(0.1, 0.5)  # Very short wait times

    @task
    def burst_analyze(self):
        """Send many requests quickly"""
        with self.client.post(
            "/api/v1/analyze",
            json={"username": "instagram"},
            catch_response=True,
        ) as response:
            if response.status_code in [202, 503, 429]:
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")

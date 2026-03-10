"""
Instagram HTTP Client - curl_cffi 기반
Direct HTTP requests to Instagram web_profile_info API
"""

import random
import asyncio
from typing import Dict, Any
from curl_cffi import requests

from app.utils.exceptions import (
    InstagramServiceError,
    ProfileNotFoundError,
    RateLimitError,
)
import structlog

logger = structlog.get_logger()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


class InstagramHTTPClient:
    """
    Instagram HTTP Client using curl_cffi for browser impersonation
    - Uses web_profile_info API for public profile data
    - Handles rate limiting and retries
    """

    BASE_URL = "https://www.instagram.com/api/v1/users/web_profile_info/"
    IG_APP_ID = "936619743392459"

    def __init__(self):
        self.session = requests.Session(impersonate="chrome120")

    def _get_headers(self) -> Dict[str, str]:
        """Generate request headers with random User-Agent"""
        return {
            "x-ig-app-id": self.IG_APP_ID,
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.instagram.com/",
        }

    async def fetch_profile(self, username: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Fetch profile data from Instagram web_profile_info API

        Args:
            username: Instagram username to fetch
            max_retries: Maximum number of retry attempts

        Returns:
            Raw JSON response from Instagram API

        Raises:
            ProfileNotFoundError: If profile doesn't exist
            RateLimitError: If rate limited by Instagram
            InstagramServiceError: For other errors
        """
        params = {"username": username}

        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(
                    self.session.get,
                    self.BASE_URL,
                    params=params,
                    headers=self._get_headers(),
                    timeout=30,
                )

                if response.status_code == 200:
                    data = response.json()
                    # Check if user exists in response
                    user_data = data.get("data", {}).get("user")
                    if not user_data:
                        raise ProfileNotFoundError(username)
                    return data

                elif response.status_code == 404:
                    raise ProfileNotFoundError(username)

                elif response.status_code == 429:
                    # Rate limited - exponential backoff
                    delay = min(300, (2 ** attempt) * 5)
                    jitter = random.uniform(0, delay * 0.1)
                    total_wait = delay + jitter
                    logger.warning(
                        "rate_limit_hit",
                        username=username,
                        attempt=attempt + 1,
                        wait_seconds=total_wait,
                    )
                    await asyncio.sleep(total_wait)
                    continue

                elif response.status_code in (401, 403):
                    raise RateLimitError(f"Access denied for {username}")

                else:
                    response.raise_for_status()

            except (ProfileNotFoundError, RateLimitError):
                raise

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(
                        "profile_fetch_failed",
                        username=username,
                        error=str(e),
                        attempt=attempt + 1,
                    )
                    raise InstagramServiceError(f"Failed to fetch profile: {str(e)}")

                wait_time = 5 * (attempt + 1)
                logger.warning(
                    "retry_after_error",
                    username=username,
                    attempt=attempt + 1,
                    wait_seconds=wait_time,
                    error=str(e),
                )
                await asyncio.sleep(wait_time)

        raise InstagramServiceError("Max retries exceeded")


# Singleton instance
http_client = InstagramHTTPClient()

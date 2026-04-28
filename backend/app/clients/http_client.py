"""
Instagram HTTP Client - curl_cffi 기반
Direct HTTP requests to Instagram web_profile_info API
"""

import re
import html as html_module
import random
import asyncio
import json
from typing import Dict, Any, Optional
from curl_cffi import requests

from app.utils.exceptions import (
    InstagramServiceError,
    ProfileNotFoundError,
    RateLimitError,
)
from app.services.circuit_breaker import instagram_circuit_breaker, CircuitBreakerOpenError
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
        self.session = requests.Session(impersonate="chrome124")
        self._session_initialized = False

    def _ensure_session(self):
        """Instagram 홈페이지 방문으로 쿠키(csrftoken 등) 초기화"""
        if self._session_initialized:
            return
        try:
            resp = self.session.get(
                "https://www.instagram.com/",
                headers={
                    "User-Agent": random.choice(USER_AGENTS),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                },
                timeout=15,
            )
            if resp.status_code == 200:
                self._session_initialized = True
                logger.info("instagram_session_initialized")
        except Exception as e:
            logger.warning("instagram_session_init_failed", error=str(e))

    def _get_headers(self) -> Dict[str, str]:
        """Generate request headers with random User-Agent"""
        headers = {
            "x-ig-app-id": self.IG_APP_ID,
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "*/*",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.instagram.com/",
            "X-Requested-With": "XMLHttpRequest",
        }
        csrf = self.session.cookies.get("csrftoken")
        if csrf:
            headers["x-csrftoken"] = csrf
        return headers

    async def _fetch_profile_internal(self, username: str, max_retries: int = 3) -> Dict[str, Any]:
        """Internal method to fetch profile data"""
        # 세션 초기화 (쿠키 획득)
        await asyncio.to_thread(self._ensure_session)

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
                    # Playwright 브라우저로 시도 → HTML 폴백 순서
                    logger.warning(
                        "instagram_api_blocked",
                        username=username,
                        status=response.status_code,
                    )
                    pw_data = await self._fetch_profile_with_playwright(username)
                    if pw_data:
                        logger.info("using_playwright_fallback", username=username)
                        return pw_data
                    fallback = await self._fetch_profile_from_html(username)
                    if fallback:
                        logger.info("using_html_fallback", username=username)
                        return fallback
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

    async def _fetch_profile_from_html(self, username: str) -> Optional[Dict[str, Any]]:
        """
        og 메타 태그를 통한 프로필 폴백 스크래핑.
        web_profile_info API가 차단됐을 때 사용.
        게시물 데이터는 제공하지 않으므로 빈 posts 리스트로 반환.
        """
        try:
            bot_session = requests.Session()
            resp = await asyncio.to_thread(
                bot_session.get,
                f"https://www.instagram.com/{username}/",
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                },
                timeout=15,
            )

            if resp.status_code != 200:
                return None

            html_text = resp.text

            # og:description: '1,149 Followers, 696 Following, 958 Posts - ...'
            og_desc_raw = re.findall(r'<meta property="og:description" content="(.*?)"', html_text)
            og_title_raw = re.findall(r'<meta property="og:title" content="(.*?)"', html_text)
            og_image_raw = re.findall(r'<meta property="og:image" content="(.*?)"', html_text)

            if not og_desc_raw:
                return None

            og_desc = html_module.unescape(og_desc_raw[0])
            og_title = html_module.unescape(og_title_raw[0]) if og_title_raw else ""
            og_image = html_module.unescape(og_image_raw[0]) if og_image_raw else ""

            # 팔로워/팔로잉/게시물 수 파싱 (영어/한국어 모두 지원)
            # English: "1,149 Followers, 696 Following, 958 Posts"
            # Korean:  "팔로워 1,149명, 팔로잉 696명, 게시물 958개"
            m = re.search(
                r"([\d,]+)\s*Followers?,\s*([\d,]+)\s*Following,\s*([\d,]+)\s*Posts?",
                og_desc
            ) or re.search(
                r"팔로워\s*([\d,]+)명,\s*팔로잉\s*([\d,]+)명,\s*게시물\s*([\d,]+)개",
                og_desc
            )
            if not m:
                return None

            followers = int(m.group(1).replace(",", ""))
            following = int(m.group(2).replace(",", ""))
            posts_count = int(m.group(3).replace(",", ""))

            # 이름/사용자명 파싱 (영어/한국어 포맷 모두 지원)
            # English: "Full Name (@username) • Instagram..."
            # Korean:  "Full Name(@username) • Instagram..."
            tm = re.search(r"^(.*?)\s*\(@([^)]+)\)", og_title)
            full_name = tm.group(1).strip() if tm else username
            parsed_username = tm.group(2) if tm else username

            # is_private 판단 (og:description에 정상 숫자가 있으면 공개)
            is_private = False

            # web_profile_info 응답 포맷으로 조립
            user_data = {
                "username": parsed_username,
                "full_name": full_name,
                "biography": "",
                "edge_followed_by": {"count": followers},
                "edge_follow": {"count": following},
                "edge_owner_to_timeline_media": {"count": posts_count, "edges": []},
                "is_private": is_private,
                "is_verified": False,
                "profile_pic_url_hd": og_image,
                "profile_pic_url": og_image,
                "external_url": "",
            }

            logger.info(
                "html_fallback_success",
                username=username,
                followers=followers,
                posts_count=posts_count,
            )
            return {"data": {"user": user_data}}

        except Exception as e:
            logger.warning("html_fallback_failed", username=username, error=str(e))
            return None

    async def _fetch_post_from_html(self, shortcode: str) -> Optional[Dict[str, Any]]:
        """
        개별 게시물 페이지를 Googlebot UA로 스크래핑.
        og: 태그에서 캡션, 좋아요, 댓글 수, 이미지 URL 추출.
        """
        try:
            bot_session = requests.Session()
            resp = await asyncio.to_thread(
                bot_session.get,
                f"https://www.instagram.com/p/{shortcode}/",
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
                },
                timeout=10,
            )

            if resp.status_code != 200:
                return None

            html_text = resp.text

            og_desc_raw = re.findall(r'<meta property="og:description" content="(.*?)"', html_text)
            og_image_raw = re.findall(r'<meta property="og:image" content="(.*?)"', html_text)

            if not og_desc_raw:
                return None

            og_desc = html_module.unescape(og_desc_raw[0])
            og_image = html_module.unescape(og_image_raw[0]) if og_image_raw else ""

            caption = og_desc
            likes = 0
            comments = 0

            # og:description 형식 파싱 시도
            # 영어: "123 Likes, 45 Comments - caption text"
            # 한국어: "좋아요 123개, 댓글 45개 - caption text"
            m = re.match(
                r'([\d,]+)\s*[Ll]ikes?,\s*([\d,]+)\s*[Cc]omments?\s*[-–]\s*(.*)',
                og_desc
            ) or re.match(
                r'좋아요\s*([\d,]+)개,\s*댓글\s*([\d,]+)개\s*[-–]\s*(.*)',
                og_desc
            )
            if m:
                likes = int(m.group(1).replace(",", ""))
                comments = int(m.group(2).replace(",", ""))
                caption = m.group(3).strip()

            hashtags = re.findall(r'#(\w+)', caption)

            return {
                "node": {
                    "id": shortcode,
                    "shortcode": shortcode,
                    "edge_media_to_caption": {"edges": [{"node": {"text": caption}}]},
                    "edge_liked_by": {"count": likes},
                    "edge_media_to_comment": {"count": comments},
                    "display_url": og_image,
                    "is_video": False,
                    "taken_at_timestamp": 0,
                    "__typename": "GraphImage",
                }
            }

        except Exception as e:
            logger.warning("fetch_post_html_failed", shortcode=shortcode, error=str(e))
            return None

    async def _fetch_profile_with_playwright(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Playwright 브라우저를 사용해 Instagram 프로필 로드.
        1단계: web_profile_info API 인터셉트 시도 (포스트 포함)
        2단계: API 차단 시 DOM에서 게시물 shortcode 추출 → 개별 페이지 스크래핑
        """
        try:
            from playwright.async_api import async_playwright

            api_data: Optional[Dict[str, Any]] = None
            profile_shortcodes: list = []

            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                    locale="ko-KR",
                    viewport={"width": 1280, "height": 800},
                )
                page = await context.new_page()

                async def on_response(response):
                    nonlocal api_data
                    if "web_profile_info" in response.url and api_data is None:
                        try:
                            data = await response.json()
                            user = data.get("data", {}).get("user")
                            if user:
                                api_data = data
                                logger.info(
                                    "playwright_api_intercepted",
                                    username=username,
                                    posts=len(user.get("edge_owner_to_timeline_media", {}).get("edges", [])),
                                )
                        except Exception:
                            pass

                page.on("response", on_response)

                try:
                    await page.goto(
                        f"https://www.instagram.com/{username}/",
                        wait_until="networkidle",
                        timeout=30000,
                    )
                except Exception:
                    pass

                # API 응답 대기 (최대 5초)
                for _ in range(10):
                    if api_data:
                        break
                    await asyncio.sleep(0.5)

                # API 차단됐으면 DOM에서 shortcode 추출
                if not api_data:
                    try:
                        profile_shortcodes = await page.evaluate("""() => {
                            const links = Array.from(document.querySelectorAll('a[href*="/p/"]'));
                            const codes = new Set();
                            links.forEach(l => {
                                const href = l.getAttribute('href') || '';
                                const match = href.match(/\\/p\\/([^\\/]+)\\//);
                                if (match) codes.add(match[1]);
                            });
                            return Array.from(codes).slice(0, 12);
                        }""")
                        logger.info(
                            "playwright_dom_shortcodes_extracted",
                            username=username,
                            count=len(profile_shortcodes),
                        )
                    except Exception as e:
                        logger.warning("dom_shortcode_extraction_failed", error=str(e))

                await browser.close()

            if api_data:
                logger.info("playwright_fetch_success", username=username)
                return api_data

            if not profile_shortcodes:
                logger.warning("playwright_no_shortcodes_found", username=username)
                return None

            # 프로필 기본 정보는 HTML 폴백으로 수집
            profile_data = await self._fetch_profile_from_html(username)
            if not profile_data:
                return None

            # 각 게시물 페이지 스크래핑 (최대 12개, 병렬 처리)
            tasks = [self._fetch_post_from_html(sc) for sc in profile_shortcodes]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            posts_edges = [r for r in results if isinstance(r, dict)]
            logger.info(
                "playwright_dom_scraping_complete",
                username=username,
                shortcodes=len(profile_shortcodes),
                scraped=len(posts_edges),
            )

            if posts_edges:
                user = profile_data["data"]["user"]
                user["edge_owner_to_timeline_media"]["edges"] = posts_edges

            return profile_data

        except Exception as e:
            logger.warning("playwright_fetch_failed", username=username, error=str(e))
            return None

    async def fetch_profile(self, username: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        Fetch profile data from Instagram web_profile_info API.
        폴백 순서: 직접 API → Playwright 브라우저 → HTML og: 태그

        Args:
            username: Instagram username to fetch
            max_retries: Maximum number of retry attempts

        Returns:
            Raw JSON response from Instagram API

        Raises:
            ProfileNotFoundError: If profile doesn't exist
            RateLimitError: If rate limited by Instagram (and fallback also fails)
            InstagramServiceError: For other errors
        """
        try:
            return await instagram_circuit_breaker.call(
                self._fetch_profile_internal, username, max_retries
            )
        except CircuitBreakerOpenError:
            logger.warning("circuit_breaker_open_trying_playwright", username=username)

        # 서킷 브레이커 열림 또는 API 차단 → Playwright 시도
        playwright_data = await self._fetch_profile_with_playwright(username)
        if playwright_data:
            return playwright_data

        # Playwright 실패 → HTML og: 태그 폴백
        logger.warning("playwright_failed_using_html_fallback", username=username)
        html_data = await self._fetch_profile_from_html(username)
        if html_data:
            return html_data

        raise RateLimitError(f"Service temporarily unavailable for {username}")


# Singleton instance
http_client = InstagramHTTPClient()

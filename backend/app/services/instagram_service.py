"""
itsmegram v2.0 - Instagram 데이터 수집 서비스
HTTP 기반 직접 요청으로 Instaloader 대체
"""

import asyncio
import re
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.models.schemas import ProfileData, PostData, InstagramData
from app.services.cache_service import cache_service
from app.services.rate_limiter import instagram_rate_limiter
from app.clients.http_client import http_client
from app.parsers.instagram_parser import parser
from app.utils.exceptions import (
    InstagramServiceError,
    ProfileNotFoundError,
    PrivateAccountError,
    RateLimitError,
)
import structlog

logger = structlog.get_logger()


class InstagramService:
    """
    Instagram 데이터 수집 서비스 v2.0
    - HTTP 기반 직접 요청
    - Rate Limiting 지원
    - 캐싱 지원
    """

    def __init__(self):
        self._client = http_client
        self._parser = parser
        self._rate_limiter = instagram_rate_limiter

    async def fetch_profile(self, username: str, use_cache: bool = True) -> ProfileData:
        """
        인스타그램 프로필 정보 수집

        Args:
            username: 인스타그램 사용자명
            use_cache: 캐시 사용 여부

        Returns:
            ProfileData: 프로필 데이터

        Raises:
            ProfileNotFoundError: 프로필을 찾을 수 없는 경우
            PrivateAccountError: 비공개 계정인 경우
            RateLimitError: Rate limit에 걸린 경우
            InstagramServiceError: 기타 에러
        """
        # 캐시 확인
        if use_cache:
            cached = await cache_service.get_cached_profile(username)
            if cached:
                logger.info("profile_cache_hit", username=username)
                return ProfileData(**cached)

        # Rate Limit 적용
        await self._rate_limiter.acquire()

        try:
            # HTTP 요청
            response_data = await self._client.fetch_profile(username)

            # 파싱
            profile_dict = self._parser.parse_profile(response_data)

            # 비공개 계정 체크
            if profile_dict.get("is_private"):
                raise PrivateAccountError(username)

            profile_data = ProfileData(**profile_dict)

            # 성공 보고 (adaptive rate limiting)
            self._rate_limiter.report_success()

            # 캐시 저장
            if use_cache:
                await cache_service.cache_profile(
                    username,
                    profile_data.model_dump(),
                    ttl=1800,  # 30분
                )

            logger.info(
                "profile_fetched",
                username=username,
                followers=profile_data.followers,
            )
            return profile_data

        except ProfileNotFoundError:
            raise
        except PrivateAccountError:
            raise
        except RateLimitError:
            self._rate_limiter.report_rate_limited()
            raise
        except Exception as e:
            logger.error("profile_fetch_error", username=username, error=str(e))
            raise InstagramServiceError(f"Failed to fetch profile: {str(e)}")

    async def fetch_posts(
        self,
        username: str,
        limit: int = 20,
        use_cache: bool = True,
    ) -> List[PostData]:
        """
        인스타그램 게시물 수집

        Args:
            username: 인스타그램 사용자명
            limit: 수집할 게시물 수 (최대 50)
            use_cache: 캐시 사용 여부

        Returns:
            List[PostData]: 게시물 데이터 목록
        """
        limit = min(limit, 50)

        # 캐시 확인
        if use_cache:
            cached = await cache_service.get_cached_posts(username, limit)
            if cached:
                return [PostData(**post) for post in cached]

        # Rate Limit 적용
        await self._rate_limiter.acquire()

        try:
            # HTTP 요청 (프로필 API에서 게시물도 함께 제공)
            response_data = await self._client.fetch_profile(username)

            # 파싱
            posts_list = self._parser.parse_posts(response_data, limit)
            posts_data = [PostData(**post) for post in posts_list]

            # 성공 보고
            self._rate_limiter.report_success()

            # 캐시 저장
            if use_cache and posts_data:
                await cache_service.cache_posts(
                    username,
                    limit,
                    [post.model_dump() for post in posts_data],
                    ttl=1800,  # 30분
                )

            logger.info(
                "posts_fetched",
                username=username,
                count=len(posts_data),
            )
            return posts_data

        except Exception as e:
            logger.error("posts_fetch_error", username=username, error=str(e))
            raise InstagramServiceError(f"Failed to fetch posts: {str(e)}")

    async def fetch_full_data(
        self,
        username: str,
        posts_limit: int = 20,
        use_cache: bool = True,
    ) -> InstagramData:
        """
        프로필과 게시물 데이터를 한번에 수집

        Args:
            username: 인스타그램 사용자명
            posts_limit: 수집할 게시물 수
            use_cache: 캐시 사용 여부

        Returns:
            InstagramData: 전체 인스타그램 데이터
        """
        # 캐시 확인 (전체 데이터)
        if use_cache:
            cached = await cache_service.get_cached_analysis(username)
            if cached:
                return InstagramData(**cached)

        # 병렬 처리
        profile, posts = await asyncio.gather(
            self.fetch_profile(username, use_cache),
            self.fetch_posts(username, posts_limit, use_cache),
        )

        return InstagramData(
            profile=profile,
            posts=posts,
            collected_at=datetime.utcnow(),
        )

    async def validate_username(self, username: str) -> Dict[str, Any]:
        """
        사용자명 유효성 검사 및 계정 존재 여부 확인

        Args:
            username: 검사할 사용자명

        Returns:
            Dict: 검사 결과
        """
        if not re.match(r"^[a-zA-Z0-9._]{1,30}$", username):
            return {
                "username": username,
                "is_valid": False,
                "exists": None,
                "is_private": None,
                "message": "Invalid username format",
            }

        try:
            await self._rate_limiter.acquire()
            response_data = await self._client.fetch_profile(username)
            profile_dict = self._parser.parse_profile(response_data)

            return {
                "username": username,
                "is_valid": True,
                "exists": True,
                "is_private": profile_dict.get("is_private", False),
                "message": "Account exists",
            }

        except ProfileNotFoundError:
            return {
                "username": username,
                "is_valid": True,
                "exists": False,
                "is_private": None,
                "message": "Account does not exist",
            }
        except Exception as e:
            return {
                "username": username,
                "is_valid": True,
                "exists": None,
                "is_private": None,
                "message": f"Error: {str(e)}",
            }

    async def clear_cache(self, username: Optional[str] = None) -> bool:
        """
        캐시 삭제

        Args:
            username: 특정 사용자의 캐시만 삭제 (None이면 전체 삭제 시도)

        Returns:
            bool: 성공 여부
        """
        try:
            if username:
                await cache_service.invalidate_profile(username)
                await cache_service.invalidate_posts(username)
                logger.info("cache_cleared_for_user", username=username)
            return True
        except Exception as e:
            logger.error("cache_clear_error", error=str(e))
            return False


# 싱글톤 인스턴스
instagram_service = InstagramService()

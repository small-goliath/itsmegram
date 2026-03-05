"""
itsmegram - 캐시 서비스
Redis 기반 캐싱 및 Rate Limiting 지원
"""

import json
from typing import Any, Optional
from datetime import timedelta

import redis.asyncio as redis
from app.config import get_settings
import structlog

logger = structlog.get_logger()


class CacheService:
    """
    Redis 기반 캐시 서비스
    - 데이터 캐싱
    - Rate Limiting 지원
    """

    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._settings = get_settings()

    async def connect(self) -> bool:
        """
        Redis 연결 초기화
        Returns:
            연결 성공 여부
        """
        if not self._settings.redis_enabled:
            logger.info("redis_disabled", message="Redis가 비활성화되어 있습니다")
            return False

        try:
            self._redis = await redis.from_url(
                self._settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            await self._redis.ping()
            logger.info("redis_connected", url=self._settings.redis_url)
            return True
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            self._redis = None
            return False

    async def disconnect(self):
        """Redis 연결 종료"""
        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("redis_disconnected")

    async def get(self, key: str) -> Optional[Any]:
        """
        캐시에서 값 조회
        Args:
            key: 캐시 키
        Returns:
            캐시된 값 또는 None
        """
        if not self._redis:
            return None

        try:
            value = await self._redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error("cache_get_error", key=key, error=str(e))
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        캐시에 값 저장
        Args:
            key: 캐시 키
            value: 저장할 값
            ttl: 만료 시간(초), None이면 기본값 사용
        Returns:
            저장 성공 여부
        """
        if not self._redis:
            return False

        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                await self._redis.setex(key, ttl, serialized)
            else:
                await self._redis.set(key, serialized)
            return True
        except Exception as e:
            logger.error("cache_set_error", key=key, error=str(e))
            return False

    async def delete(self, key: str) -> bool:
        """
        캐시에서 값 삭제
        Args:
            key: 캐시 키
        Returns:
            삭제 성공 여부
        """
        if not self._redis:
            return False

        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error("cache_delete_error", key=key, error=str(e))
            return False

    async def exists(self, key: str) -> bool:
        """
        키 존재 여부 확인
        Args:
            key: 캐시 키
        Returns:
            키 존재 여부
        """
        if not self._redis:
            return False

        try:
            return await self._redis.exists(key) > 0
        except Exception as e:
            logger.error("cache_exists_error", key=key, error=str(e))
            return False

    # Rate Limiting 메서드

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:
        """
        Rate Limiting 체크 (Sliding Window)
        Args:
            key: rate limit 키 (예: "ratelimit:192.168.1.1:analyze")
            limit: 허용 최대 요청 수
            window_seconds: 시간 윈도우(초)
        Returns:
            (허용 여부, 현재 요청 수, 남은 시간(초))
        """
        if not self._redis:
            # Redis가 없으면 rate limiting 없이 허용
            return True, 0, window_seconds

        try:
            pipe = self._redis.pipeline()
            now = int(__import__('time').time())
            window_start = now - window_seconds

            # 이전 윈도우의 요청 삭제
            pipe.zremrangebyscore(key, 0, window_start)
            # 현재 요청 수 확인
            pipe.zcard(key)
            # 현재 요청 추가
            pipe.zadd(key, {str(now): now})
            # 만료 시간 설정
            pipe.expire(key, window_seconds)

            results = await pipe.execute()
            current_count = results[1]

            if current_count > limit:
                # 제한 초과 - 추가한 요청 제거
                await self._redis.zrem(key, str(now))
                ttl = await self._redis.ttl(key)
                return False, current_count - 1, max(ttl, 0)

            ttl = await self._redis.ttl(key)
            return True, current_count, max(ttl, window_seconds)

        except Exception as e:
            logger.error("rate_limit_check_error", key=key, error=str(e))
            # 에러 시 허용 (fail open)
            return True, 0, window_seconds

    async def get_rate_limit_info(
        self,
        key: str,
        window_seconds: int,
    ) -> tuple[int, int]:
        """
        현재 rate limit 상태 조회
        Args:
            key: rate limit 키
            window_seconds: 시간 윈도우(초)
        Returns:
            (현재 요청 수, 남은 시간(초))
        """
        if not self._redis:
            return 0, window_seconds

        try:
            now = int(__import__('time').time())
            window_start = now - window_seconds

            # 현재 윈도우 내 요청 수
            count = await self._redis.zcount(key, window_start, now)
            ttl = await self._redis.ttl(key)

            return count, max(ttl, 0)
        except Exception as e:
            logger.error("rate_limit_info_error", key=key, error=str(e))
            return 0, window_seconds


    # Analysis 캐싱 메서드

    async def get_cached_analysis(self, username: str) -> Optional[dict]:
        """
        캐시된 분석 결과 조회
        같은 username 1시간 내 재요청 시 캐시된 결과 반환

        Args:
            username: 인스타그램 사용자명

        Returns:
            캐시된 분석 결과 또는 None
        """
        return await self.get(f"analysis:{username.lower()}")

    async def cache_analysis(
        self,
        username: str,
        data: dict,
        ttl: int = 3600
    ) -> bool:
        """
        분석 결과 캐싱 (기본 1시간)

        Args:
            username: 인스타그램 사용자명
            data: 캐싱할 분석 데이터
            ttl: 만료 시간(초), 기본 3600(1시간)

        Returns:
            저장 성공 여부
        """
        return await self.set(f"analysis:{username.lower()}", data, ttl=ttl)

    async def get_cached_profile(self, username: str) -> Optional[dict]:
        """
        캐시된 인스타그램 프로필 조회 (30분 TTL)

        Args:
            username: 인스타그램 사용자명

        Returns:
            캐시된 프로필 데이터 또는 None
        """
        return await self.get(f"instagram:profile:{username.lower()}")

    async def cache_profile(
        self,
        username: str,
        data: dict,
        ttl: int = 1800
    ) -> bool:
        """
        인스타그램 프로필 캐싱 (기본 30분)

        Args:
            username: 인스타그램 사용자명
            data: 캐싱할 프로필 데이터
            ttl: 만료 시간(초), 기본 1800(30분)

        Returns:
            저장 성공 여부
        """
        return await self.set(f"instagram:profile:{username.lower()}", data, ttl=ttl)

    async def get_cached_posts(
        self,
        username: str,
        limit: int
    ) -> Optional[list]:
        """
        캐시된 인스타그램 게시물 조회 (30분 TTL)

        Args:
            username: 인스타그램 사용자명
            limit: 조회한 게시물 수

        Returns:
            캐시된 게시물 목록 또는 None
        """
        return await self.get(f"instagram:posts:{username.lower()}:{limit}")

    async def cache_posts(
        self,
        username: str,
        limit: int,
        data: list,
        ttl: int = 1800
    ) -> bool:
        """
        인스타그램 게시물 캐싱 (기본 30분)

        Args:
            username: 인스타그램 사용자명
            limit: 조회한 게시물 수
            data: 캐싱할 게시물 목록
            ttl: 만료 시간(초), 기본 1800(30분)

        Returns:
            저장 성공 여부
        """
        return await self.set(
            f"instagram:posts:{username.lower()}:{limit}",
            data,
            ttl=ttl
        )

    async def invalidate_analysis(self, username: str) -> bool:
        """
        특정 사용자의 분석 결과 캐시 무효화

        Args:
            username: 인스타그램 사용자명

        Returns:
            삭제 성공 여부
        """
        return await self.delete(f"analysis:{username.lower()}")

    async def invalidate_profile(self, username: str) -> bool:
        """
        특정 사용자의 프로필 캐시 무효화

        Args:
            username: 인스타그램 사용자명

        Returns:
            삭제 성공 여부
        """
        return await self.delete(f"instagram:profile:{username.lower()}")

    async def invalidate_posts(self, username: str, limit: Optional[int] = None) -> bool:
        """
        특정 사용자의 게시물 캐시 무효화

        Args:
            username: 인스타그램 사용자명
            limit: 특정 limit의 캐시만 삭제 (None이면 모든 limit)

        Returns:
            삭제 성공 여부
        """
        if limit is not None:
            return await self.delete(f"instagram:posts:{username.lower()}:{limit}")

        # 모든 limit에 대해 삭제 시도
        success = True
        for l in [12, 20, 30, 50]:
            if not await self.delete(f"instagram:posts:{username.lower()}:{l}"):
                success = False
        return success


# 싱글톤 인스턴스
cache_service = CacheService()

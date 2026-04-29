"""
itsmegram - 리포트 저장소 서비스
Redis 또는 메모리 캐시를 사용한 리포트 데이터 저장/조회
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
import asyncio

import structlog

from app.models.report import Report
from app.utils.exceptions import (
    StorageError,
    ReportNotFoundError,
    ReportExpiredError,
)

logger = structlog.get_logger()


class BaseStorage(ABC):
    """저장소 추상 기본 클래스"""

    @abstractmethod
    async def save_report(self, report: Report) -> str:
        """리포트 저장"""
        pass

    @abstractmethod
    async def get_report(self, report_id: str) -> Optional[Report]:
        """리포트 조회"""
        pass

    @abstractmethod
    async def delete_report(self, report_id: str) -> bool:
        """리포트 삭제"""
        pass

    @abstractmethod
    async def update_report_status(
        self,
        report_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """리포트 상태 업데이트"""
        pass

    @abstractmethod
    async def report_exists(self, report_id: str) -> bool:
        """리포트 존재 여부 확인"""
        pass

    @abstractmethod
    async def get_report_id_by_username(self, username: str) -> Optional[str]:
        """username으로 완료된 리포트 ID 조회"""
        pass

    @abstractmethod
    async def set_username_report_index(self, username: str, report_id: str, ttl_hours: int) -> None:
        """username → report_id 인덱스 저장"""
        pass

    @abstractmethod
    async def delete_username_report_index(self, username: str) -> None:
        """username 인덱스 삭제"""
        pass


class MemoryStorage(BaseStorage):
    """메모리 기반 저장소 (Redis 없을 때 폴백)"""

    def __init__(self, ttl_hours: int = 168):
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._username_index: Dict[str, str] = {}  # username → report_id
        self._username_expires: Dict[str, datetime] = {}  # username → expires_at
        self._ttl_hours = ttl_hours
        self._lock = asyncio.Lock()
        logger.info("memory_storage_initialized", ttl_hours=ttl_hours)

    def _get_key(self, report_id: str) -> str:
        """저장소 키 생성"""
        return f"report:{report_id}"

    def _is_expired(self, data: Dict[str, Any]) -> bool:
        """데이터가 만료되었는지 확인"""
        expires_at_str = data.get("expires_at")
        if not expires_at_str:
            return False
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
            return datetime.utcnow() > expires_at
        except (ValueError, TypeError):
            return False

    async def save_report(self, report: Report) -> str:
        """리포트를 메모리에 저장"""
        async with self._lock:
            key = self._get_key(report.id)
            self._storage[key] = json.loads(report.model_dump_json())
            logger.info(
                "report_saved_to_memory",
                report_id=report.id,
                username=report.username,
                status=report.status
            )
            return report.id

    async def get_report(self, report_id: str) -> Optional[Report]:
        """메모리에서 리포트 조회"""
        async with self._lock:
            key = self._get_key(report_id)
            data = self._storage.get(key)

            if not data:
                logger.debug("report_not_found_in_memory", report_id=report_id)
                return None

            # 만료 확인
            if self._is_expired(data):
                del self._storage[key]
                logger.info("report_expired_removed", report_id=report_id)
                raise ReportExpiredError(report_id)

            try:
                report = Report.model_validate(data)
                logger.debug("report_found_in_memory", report_id=report_id)
                return report
            except Exception as e:
                logger.error("report_validation_error", report_id=report_id, error=str(e))
                return None

    async def delete_report(self, report_id: str) -> bool:
        """메모리에서 리포트 삭제"""
        async with self._lock:
            key = self._get_key(report_id)
            if key in self._storage:
                del self._storage[key]
                logger.info("report_deleted_from_memory", report_id=report_id)
                return True
            return False

    async def update_report_status(
        self,
        report_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """메모리에서 리포트 상태 업데이트"""
        async with self._lock:
            key = self._get_key(report_id)
            data = self._storage.get(key)

            if not data:
                logger.warning("report_not_found_for_update", report_id=report_id)
                return False

            # 만료 확인
            if self._is_expired(data):
                del self._storage[key]
                raise ReportExpiredError(report_id)

            data["status"] = status
            if error_message is not None:
                data["error_message"] = error_message

            self._storage[key] = data
            logger.info("report_status_updated", report_id=report_id, status=status)
            return True

    async def report_exists(self, report_id: str) -> bool:
        """리포트 존재 여부 확인"""
        async with self._lock:
            key = self._get_key(report_id)
            data = self._storage.get(key)

            if not data:
                return False

            # 만료 확인
            if self._is_expired(data):
                del self._storage[key]
                return False

            return True

    async def get_report_id_by_username(self, username: str) -> Optional[str]:
        """username으로 완료된 리포트 ID 조회"""
        async with self._lock:
            report_id = self._username_index.get(username)
            if not report_id:
                return None
            # 인덱스 만료 확인
            expires_at = self._username_expires.get(username)
            if expires_at and datetime.utcnow() > expires_at:
                del self._username_index[username]
                del self._username_expires[username]
                return None
            return report_id

    async def set_username_report_index(self, username: str, report_id: str, ttl_hours: int) -> None:
        """username → report_id 인덱스 저장"""
        async with self._lock:
            self._username_index[username] = report_id
            self._username_expires[username] = datetime.utcnow() + timedelta(hours=ttl_hours)

    async def delete_username_report_index(self, username: str) -> None:
        """username 인덱스 삭제"""
        async with self._lock:
            self._username_index.pop(username, None)
            self._username_expires.pop(username, None)

    async def cleanup_expired(self) -> int:
        """만료된 리포트 정리"""
        async with self._lock:
            expired_keys = [
                key for key, data in self._storage.items()
                if self._is_expired(data)
            ]
            for key in expired_keys:
                del self._storage[key]

            # 만료된 username 인덱스 정리
            now = datetime.utcnow()
            expired_usernames = [
                u for u, exp in self._username_expires.items()
                if now > exp
            ]
            for u in expired_usernames:
                self._username_index.pop(u, None)
                self._username_expires.pop(u, None)

            if expired_keys:
                logger.info("expired_reports_cleaned", count=len(expired_keys))
            return len(expired_keys)


class RedisStorage(BaseStorage):
    """Redis 기반 저장소"""

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        ttl_hours: int = 168
    ):
        self.url = url
        self.ttl = timedelta(hours=ttl_hours)
        self._redis = None
        self._connected = False
        from urllib.parse import urlparse
        try:
            p = urlparse(url)
            safe = url.replace(f":{p.password}@", ":****@") if p.password else url
        except Exception:
            safe = url
        logger.info("redis_storage_initialized", url=safe)

    async def _get_redis(self):
        """Redis 연결 가져오기 (지연 로딩)"""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(
                    self.url,
                    decode_responses=True
                )
                # 연결 테스트
                await self._redis.ping()
                self._connected = True
                logger.info("redis_connected")
            except Exception as e:
                logger.error("redis_connection_failed", error=str(e))
                self._connected = False
                raise StorageError(f"Failed to connect to Redis: {str(e)}", "redis_connection_error")
        return self._redis

    def _get_key(self, report_id: str) -> str:
        """Redis 키 생성"""
        return f"report:{report_id}"

    async def save_report(self, report: Report) -> str:
        """리포트를 Redis에 저장"""
        try:
            redis = await self._get_redis()
            key = self._get_key(report.id)
            report_json = report.model_dump_json()

            await redis.setex(key, self.ttl, report_json)

            logger.info(
                "report_saved_to_redis",
                report_id=report.id,
                username=report.username,
                status=report.status,
                ttl_seconds=self.ttl.total_seconds()
            )
            return report.id

        except Exception as e:
            logger.error("redis_save_error", report_id=report.id, error=str(e))
            raise StorageError(f"Failed to save report: {str(e)}", "redis_save_error")

    async def get_report(self, report_id: str) -> Optional[Report]:
        """Redis에서 리포트 조회"""
        try:
            redis = await self._get_redis()
            key = self._get_key(report_id)
            data = await redis.get(key)

            if not data:
                logger.debug("report_not_found_in_redis", report_id=report_id)
                return None

            try:
                report = Report.model_validate_json(data)

                # 만료 확인
                if report.is_expired():
                    await redis.delete(key)
                    logger.info("report_expired_deleted", report_id=report_id)
                    raise ReportExpiredError(report_id)

                logger.debug("report_found_in_redis", report_id=report_id)
                return report

            except Exception as e:
                logger.error("report_validation_error", report_id=report_id, error=str(e))
                return None

        except ReportExpiredError:
            raise
        except Exception as e:
            logger.error("redis_get_error", report_id=report_id, error=str(e))
            raise StorageError(f"Failed to get report: {str(e)}", "redis_get_error")

    async def delete_report(self, report_id: str) -> bool:
        """Redis에서 리포트 삭제"""
        try:
            redis = await self._get_redis()
            key = self._get_key(report_id)
            result = await redis.delete(key)

            if result:
                logger.info("report_deleted_from_redis", report_id=report_id)
                return True
            return False

        except Exception as e:
            logger.error("redis_delete_error", report_id=report_id, error=str(e))
            raise StorageError(f"Failed to delete report: {str(e)}", "redis_delete_error")

    async def update_report_status(
        self,
        report_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """Redis에서 리포트 상태 업데이트"""
        try:
            report = await self.get_report(report_id)

            if not report:
                logger.warning("report_not_found_for_update", report_id=report_id)
                return False

            report.status = status
            if error_message is not None:
                report.error_message = error_message

            await self.save_report(report)
            logger.info("report_status_updated", report_id=report_id, status=status)
            return True

        except ReportExpiredError:
            raise
        except Exception as e:
            logger.error("redis_update_error", report_id=report_id, error=str(e))
            raise StorageError(f"Failed to update report: {str(e)}", "redis_update_error")

    async def report_exists(self, report_id: str) -> bool:
        """리포트 존재 여부 확인"""
        try:
            redis = await self._get_redis()
            key = self._get_key(report_id)
            exists = await redis.exists(key)
            return bool(exists)

        except Exception as e:
            logger.error("redis_exists_error", report_id=report_id, error=str(e))
            return False

    def _get_username_key(self, username: str) -> str:
        """username 인덱스 Redis 키"""
        return f"username_report:{username}"

    async def get_report_id_by_username(self, username: str) -> Optional[str]:
        """username으로 완료된 리포트 ID 조회"""
        try:
            redis = await self._get_redis()
            report_id = await redis.get(self._get_username_key(username))
            return report_id if report_id else None
        except Exception as e:
            logger.warning("redis_username_index_get_error", username=username, error=str(e))
            return None

    async def set_username_report_index(self, username: str, report_id: str, ttl_hours: int) -> None:
        """username → report_id 인덱스 저장"""
        try:
            redis = await self._get_redis()
            await redis.setex(
                self._get_username_key(username),
                timedelta(hours=ttl_hours),
                report_id
            )
        except Exception as e:
            logger.warning("redis_username_index_set_error", username=username, error=str(e))

    async def delete_username_report_index(self, username: str) -> None:
        """username 인덱스 삭제"""
        try:
            redis = await self._get_redis()
            await redis.delete(self._get_username_key(username))
        except Exception as e:
            logger.warning("redis_username_index_delete_error", username=username, error=str(e))

    async def close(self):
        """Redis 연결 종료"""
        if self._redis:
            await self._redis.close()
            self._connected = False
            logger.info("redis_connection_closed")


class ReportStorage:
    """
    리포트 저장소 (Redis 우선, 실패 시 메모리 폴백)
    """

    def __init__(
        self,
        ttl_hours: Optional[int] = None
    ):
        self._redis_storage: Optional[RedisStorage] = None
        self._memory_storage: Optional[MemoryStorage] = None
        self._using_redis = False

        # pydantic Settings에서 설정 로드
        from app.config import get_settings
        settings = get_settings()

        self.redis_url = settings.redis_url
        self.ttl_hours = ttl_hours or settings.report_ttl_hours
        self._redis_enabled = settings.redis_enabled

        # 비밀번호 마스킹한 URL로 로그
        from urllib.parse import urlparse
        safe_url = self.redis_url
        try:
            p = urlparse(self.redis_url)
            if p.password:
                safe_url = self.redis_url.replace(f":{p.password}@", ":****@")
        except Exception:
            pass

        logger.info(
            "report_storage_initialized",
            redis_enabled=self._redis_enabled,
            redis_url=safe_url,
            ttl_hours=self.ttl_hours
        )

    async def _get_storage(self) -> BaseStorage:
        """사용 가능한 저장소 가져오기"""
        # Redis가 이미 연결된 경우
        if self._using_redis and self._redis_storage:
            return self._redis_storage

        # REDIS_ENABLED=false 면 메모리 사용
        if not self._redis_enabled:
            if self._memory_storage is None:
                self._memory_storage = MemoryStorage(ttl_hours=self.ttl_hours)
                logger.info("storage_using_memory", reason="REDIS_ENABLED=false", ttl_hours=self.ttl_hours)
            return self._memory_storage

        # Redis 연결 시도 (최초 연결 또는 재연결)
        try:
            if self._redis_storage is None:
                self._redis_storage = RedisStorage(
                    url=self.redis_url,
                    ttl_hours=self.ttl_hours
                )
            # 연결 테스트 (재연결 포함)
            await self._redis_storage._get_redis()
            self._using_redis = True
            logger.info(
                "storage_redis_connected",
                redis_url="(url logged at init)",
                ttl_hours=self.ttl_hours
            )
            return self._redis_storage

        except Exception as e:
            self._using_redis = False
            logger.warning(
                "storage_redis_failed_fallback_to_memory",
                error=str(e)
            )
            # 메모리 저장소로 폴백 (재연결 시도를 위해 _redis_storage는 유지)
            if self._memory_storage is None:
                self._memory_storage = MemoryStorage(ttl_hours=self.ttl_hours)
            return self._memory_storage

    async def save_report(self, report: Report) -> str:
        """리포트 저장"""
        storage = await self._get_storage()
        return await storage.save_report(report)

    async def get_report(self, report_id: str) -> Optional[Report]:
        """리포트 조회"""
        storage = await self._get_storage()
        return await storage.get_report(report_id)

    async def delete_report(self, report_id: str) -> bool:
        """리포트 삭제"""
        storage = await self._get_storage()
        return await storage.delete_report(report_id)

    async def update_report_status(
        self,
        report_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """리포트 상태 업데이트"""
        storage = await self._get_storage()
        return await storage.update_report_status(report_id, status, error_message)

    async def report_exists(self, report_id: str) -> bool:
        """리포트 존재 여부 확인"""
        storage = await self._get_storage()
        return await storage.report_exists(report_id)

    async def get_report_id_by_username(self, username: str) -> Optional[str]:
        """username으로 완료된 리포트 ID 조회"""
        storage = await self._get_storage()
        return await storage.get_report_id_by_username(username)

    async def set_username_report_index(self, username: str, report_id: str, ttl_hours: int) -> None:
        """username → report_id 인덱스 저장"""
        storage = await self._get_storage()
        await storage.set_username_report_index(username, report_id, ttl_hours)

    async def delete_username_report_index(self, username: str) -> None:
        """username 인덱스 삭제"""
        storage = await self._get_storage()
        await storage.delete_username_report_index(username)

    def is_using_redis(self) -> bool:
        """Redis 사용 여부 확인"""
        return self._using_redis

    async def cleanup_expired(self) -> int:
        """만료된 리포트 정리 (메모리 저장소용)"""
        if self._memory_storage:
            return await self._memory_storage.cleanup_expired()
        return 0

    async def close(self):
        """저장소 연결 종료"""
        if self._redis_storage:
            await self._redis_storage.close()


# 싱글톤 인스턴스
report_storage = ReportStorage()

"""
itsmegram - 리포트 저장소 테스트
ReportStorage, MemoryStorage, RedisStorage 테스트
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.report import Report, ReportSection
from app.services.storage_service import (
    MemoryStorage,
    ReportStorage,
    ReportNotFoundError,
    ReportExpiredError,
)


class TestMemoryStorage:
    """메모리 저장소 테스트"""

    @pytest.fixture
    def storage(self):
        return MemoryStorage(ttl_hours=24)

    @pytest.fixture
    def sample_report(self):
        return Report(
            id=str(uuid4()),
            username="testuser",
            basic_metrics={"avg_likes": 75.5, "engagement_rate": 60.0},
            content_tendency={"categories": ["여행", "일상"]},
            lifestyle={"interests": ["사진", "음식"]},
            personality={"extroversion": "외향적"},
            network={"engagement_quality": "높음"},
            growth_potential={"trend": "상승"},
            summary="테스트 리포트 요약입니다.",
            profile_image_url="https://example.com/profile.jpg",
            collected_posts_count=20,
            status="completed",
        )

    @pytest.mark.asyncio
    async def test_save_and_get_report(self, storage, sample_report):
        """리포트 저장 및 조회 테스트"""
        # 저장
        report_id = await storage.save_report(sample_report)
        assert report_id == sample_report.id

        # 조회
        retrieved = await storage.get_report(report_id)
        assert retrieved is not None
        assert retrieved.id == sample_report.id
        assert retrieved.username == sample_report.username
        assert retrieved.status == sample_report.status

    @pytest.mark.asyncio
    async def test_get_nonexistent_report(self, storage):
        """존재하지 않는 리포트 조회 테스트"""
        retrieved = await storage.get_report("nonexistent-id")
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_report(self, storage, sample_report):
        """리포트 삭제 테스트"""
        # 저장
        report_id = await storage.save_report(sample_report)

        # 삭제
        result = await storage.delete_report(report_id)
        assert result is True

        # 조회 시 없어야 함
        retrieved = await storage.get_report(report_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_report(self, storage):
        """존재하지 않는 리포트 삭제 테스트"""
        result = await storage.delete_report("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_update_report_status(self, storage, sample_report):
        """리포트 상태 업데이트 테스트"""
        # 저장
        report_id = await storage.save_report(sample_report)

        # 상태 업데이트
        result = await storage.update_report_status(
            report_id, "failed", "Test error message"
        )
        assert result is True

        # 확인
        retrieved = await storage.get_report(report_id)
        assert retrieved.status == "failed"
        assert retrieved.error_message == "Test error message"

    @pytest.mark.asyncio
    async def test_update_nonexistent_report(self, storage):
        """존재하지 않는 리포트 상태 업데이트 테스트"""
        result = await storage.update_report_status(
            "nonexistent-id", "failed", "Error"
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_report_exists(self, storage, sample_report):
        """리포트 존재 여부 확인 테스트"""
        # 저장 전
        exists = await storage.report_exists(sample_report.id)
        assert exists is False

        # 저장
        await storage.save_report(sample_report)

        # 저장 후
        exists = await storage.report_exists(sample_report.id)
        assert exists is True

    @pytest.mark.asyncio
    async def test_expired_report(self, storage):
        """만료된 리포트 테스트"""
        # 만료된 리포트 생성
        expired_report = Report(
            id=str(uuid4()),
            username="expireduser",
            created_at=datetime.utcnow() - timedelta(hours=25),
            expires_at=datetime.utcnow() - timedelta(hours=1),
            status="completed",
        )

        # 저장
        await storage.save_report(expired_report)

        # 조회 시 만료 예외 발생
        with pytest.raises(ReportExpiredError):
            await storage.get_report(expired_report.id)

    @pytest.mark.asyncio
    async def test_cleanup_expired(self, storage):
        """만료된 리포트 정리 테스트"""
        # 만료된 리포트 생성
        expired_report = Report(
            id=str(uuid4()),
            username="expireduser",
            created_at=datetime.utcnow() - timedelta(hours=25),
            expires_at=datetime.utcnow() - timedelta(hours=1),
            status="completed",
        )

        # 정상 리포트 생성
        normal_report = Report(
            id=str(uuid4()),
            username="normaluser",
            status="completed",
        )

        # 저장
        await storage.save_report(expired_report)
        await storage.save_report(normal_report)

        # 정리
        cleaned_count = await storage.cleanup_expired()
        assert cleaned_count == 1

        # 확인
        exists_expired = await storage.report_exists(expired_report.id)
        exists_normal = await storage.report_exists(normal_report.id)
        assert exists_expired is False
        assert exists_normal is True


class TestReportStorage:
    """통합 ReportStorage 테스트"""

    @pytest.fixture
    def storage(self):
        return ReportStorage()

    @pytest.fixture
    def sample_report(self):
        return Report(
            id=str(uuid4()),
            username="testuser",
            basic_metrics={"avg_likes": 75.5},
            status="completed",
        )

    @pytest.mark.asyncio
    async def test_storage_initialization(self, storage):
        """저장소 초기화 테스트"""
        assert storage.host is not None
        assert storage.port is not None
        assert storage.ttl_hours > 0

    @pytest.mark.asyncio
    async def test_fallback_to_memory(self, storage, sample_report):
        """Redis 실패 시 메모리로 폴백 테스트"""
        # Redis가 없는 환경에서는 메모리 저장소로 폴백
        storage._using_redis = False
        storage._memory_storage = MemoryStorage()

        # 저장 및 조회
        report_id = await storage.save_report(sample_report)
        retrieved = await storage.get_report(report_id)

        assert retrieved is not None
        assert retrieved.id == sample_report.id

    @pytest.mark.asyncio
    async def test_is_using_redis(self, storage):
        """Redis 사용 여부 확인 테스트"""
        # 초기 상태
        is_redis = storage.is_using_redis()
        assert isinstance(is_redis, bool)


class TestConcurrency:
    """동시성 테스트"""

    @pytest.mark.asyncio
    async def test_concurrent_report_creation(self):
        """동시 리포트 생성 테스트"""
        storage = MemoryStorage()
        report_ids = []

        async def create_report(index: int):
            report = Report(
                id=str(uuid4()),
                username=f"user{index}",
                status="completed",
            )
            report_id = await storage.save_report(report)
            report_ids.append(report_id)
            return report_id

        # 동시에 10개 리포트 생성
        tasks = [create_report(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert len(set(results)) == 10  # 모든 ID가 고유해야 함

        # 모든 리포트 조회 확인
        for report_id in results:
            retrieved = await storage.get_report(report_id)
            assert retrieved is not None

    @pytest.mark.asyncio
    async def test_concurrent_read_write(self):
        """동시 읽기/쓰기 테스트"""
        storage = MemoryStorage()
        report = Report(
            id=str(uuid4()),
            username="concurrentuser",
            status="processing",
        )
        await storage.save_report(report)

        async def read_report():
            for _ in range(10):
                await storage.get_report(report.id)
                await asyncio.sleep(0.01)

        async def update_report():
            for i in range(10):
                await storage.update_report_status(
                    report.id,
                    "completed" if i % 2 == 0 else "processing"
                )
                await asyncio.sleep(0.01)

        # 동시에 읽기와 쓰기 수행
        await asyncio.gather(
            read_report(),
            update_report(),
            read_report(),
        )

        # 최종 상태 확인
        final = await storage.get_report(report.id)
        assert final is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

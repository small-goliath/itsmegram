"""
itsmegram - 리포트 서비스 테스트
ReportService 테스트
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.report import Report
from app.models.schemas import InstagramData, ProfileData, PostData
from app.services.report_service import ReportService, ReportCreationError
from app.services.storage_service import MemoryStorage


class MockInstagramService:
    """Mock Instagram 서비스"""

    async def fetch_full_data(self, username: str, posts_limit: int = 20, use_cache: bool = True):
        return InstagramData(
            profile=ProfileData(
                username=username,
                full_name=f"{username.title()} User",
                biography="Test biography",
                followers=1000,
                following=500,
                posts_count=100,
                profile_pic_url="https://example.com/profile.jpg",
            ),
            posts=[
                PostData(
                    post_id="123",
                    caption="Test post",
                    likes=100,
                    comments=10,
                    hashtags=["test", "photo"],
                )
            ],
        )


class MockAIService:
    """Mock AI 서비스"""

    async def analyze_profile(self, instagram_data):
        return {
            "basic_metrics": {
                "avg_likes": 75.5,
                "engagement_rate": 60.0,
                "post_type_ratio": {"image": 0.6, "video": 0.3, "carousel": 0.1}
            },
            "content_tendency": {
                "categories": ["여행", "일상"],
                "visual_style": "밝은 스타일로 보입니다",
                "text_style": "친근한 문체로 보입니다",
                "hashtag_pattern": ["일상", "여행"]
            },
            "lifestyle": {
                "interests": ["사진", "여행"],
                "activity_pattern": "주말 활동이 많은 것으로 보입니다",
                "consumption": ["체험 중심"]
            },
            "personality": {
                "extroversion": "외향적인 것으로 보입니다",
                "expression_strength": 80.0,
                "communication": "친근한 스타일로 보입니다"
            },
            "network": {
                "engagement_quality": "높은 것으로 보입니다",
                "community_type": "관심사 기반으로 보입니다"
            },
            "growth_potential": {
                "trend": "상승세로 보입니다",
                "consistency": "꾸준한 것으로 보입니다",
                "suggestions": ["릴스 추가", "해시태그 다양화"]
            },
            "summary": "테스트 요약입니다."
        }


class TestReportService:
    """ReportService 테스트"""

    @pytest.fixture
    def storage(self):
        return MemoryStorage()

    @pytest.fixture
    def mock_instagram_service(self):
        return MockInstagramService()

    @pytest.fixture
    def mock_ai_service(self):
        return MockAIService()

    @pytest.fixture
    def report_service(self, storage, mock_instagram_service, mock_ai_service):
        return ReportService(
            storage=storage,
            ai_service=mock_ai_service,
            instagram_service=mock_instagram_service,
        )

    @pytest.mark.asyncio
    async def test_create_report_success(self, report_service):
        """리포트 생성 성공 테스트"""
        report_id = await report_service.create_report("testuser")

        assert report_id is not None
        assert len(report_id) > 0

        # 저장된 리포트 확인
        report = await report_service.get_report(report_id)
        assert report is not None
        assert report.username == "testuser"
        assert report.status == "completed"
        assert report.summary == "테스트 요약입니다."
        assert report.collected_posts_count == 1

    @pytest.mark.asyncio
    async def test_get_report_not_found(self, report_service):
        """존재하지 않는 리포트 조회 테스트"""
        with pytest.raises(Exception) as exc_info:
            await report_service.get_report("nonexistent-id")

    @pytest.mark.asyncio
    async def test_delete_report(self, report_service):
        """리포트 삭제 테스트"""
        # 생성
        report_id = await report_service.create_report("testuser")

        # 삭제
        result = await report_service.delete_report(report_id)
        assert result is True

        # 조회 시 예외 발생
        with pytest.raises(Exception):
            await report_service.get_report(report_id)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_report(self, report_service):
        """존재하지 않는 리포트 삭제 테스트"""
        result = await report_service.delete_report("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_report_status(self, report_service):
        """리포트 상태 조회 테스트"""
        # 생성
        report_id = await report_service.create_report("testuser")

        # 상태 조회
        status = await report_service.get_report_status(report_id)

        assert status["report_id"] == report_id
        assert status["username"] == "testuser"
        assert status["status"] == "completed"
        assert "created_at" in status
        assert "expires_at" in status

    @pytest.mark.asyncio
    async def test_get_report_status_not_found(self, report_service):
        """존재하지 않는 리포트 상태 조회 테스트"""
        status = await report_service.get_report_status("nonexistent-id")

        assert status["report_id"] == "nonexistent-id"
        assert status["status"] == "not_found"

    @pytest.mark.asyncio
    async def test_report_data_structure(self, report_service):
        """리포트 데이터 구조 검증 테스트"""
        report_id = await report_service.create_report("testuser")
        report = await report_service.get_report(report_id)

        # 필수 필드 확인
        assert report.id is not None
        assert report.username == "testuser"
        assert report.created_at is not None
        assert report.expires_at is not None
        assert report.status == "completed"

        # AI 분석 결과 필드 확인
        assert "avg_likes" in report.basic_metrics
        assert "categories" in report.content_tendency
        assert "interests" in report.lifestyle
        assert "extroversion" in report.personality
        assert "engagement_quality" in report.network
        assert "trend" in report.growth_potential
        assert report.summary != ""

        # 메타데이터 확인
        assert report.profile_image_url == "https://example.com/profile.jpg"
        assert report.collected_posts_count == 1


class TestReportServiceErrors:
    """ReportService 에러 처리 테스트"""

    @pytest.fixture
    def storage(self):
        return MemoryStorage()

    @pytest.fixture
    def report_service_with_failing_instagram(self, storage):
        """Instagram 서비스가 실패하는 경우"""
        class FailingInstagramService:
            async def fetch_full_data(self, *args, **kwargs):
                from app.services.instagram_service import ProfileNotFoundError
                raise ProfileNotFoundError("testuser")

        return ReportService(
            storage=storage,
            ai_service=MockAIService(),
            instagram_service=FailingInstagramService(),
        )

    @pytest.fixture
    def report_service_with_failing_ai(self, storage):
        """AI 서비스가 실패하는 경우"""
        class FailingAIService:
            async def analyze_profile(self, *args, **kwargs):
                from app.services.ai_service import AIServiceError
                raise AIServiceError("AI analysis failed")

        return ReportService(
            storage=storage,
            ai_service=FailingAIService(),
            instagram_service=MockInstagramService(),
        )

    @pytest.mark.asyncio
    async def test_create_report_instagram_error(self, report_service_with_failing_instagram):
        """Instagram 오류 시 리포트 생성 테스트"""
        with pytest.raises(ReportCreationError) as exc_info:
            await report_service_with_failing_instagram.create_report("testuser")

        assert "not found" in str(exc_info.value).lower() or "Profile" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_report_ai_error(self, report_service_with_failing_ai):
        """AI 오류 시 리포트 생성 테스트"""
        with pytest.raises(ReportCreationError) as exc_info:
            await report_service_with_failing_ai.create_report("testuser")

        assert "AI" in str(exc_info.value) or "failed" in str(exc_info.value).lower()


class TestReportExpiration:
    """리포트 만료 테스트"""

    @pytest.mark.asyncio
    async def test_expired_report_handling(self):
        """만료된 리포트 처리 테스트"""
        storage = MemoryStorage()

        # 만료된 리포트 생성
        expired_report = Report(
            id=str(uuid4()),
            username="expireduser",
            created_at=datetime.utcnow() - timedelta(hours=25),
            expires_at=datetime.utcnow() - timedelta(hours=1),
            status="completed",
        )

        await storage.save_report(expired_report)

        # ReportService 생성
        service = ReportService(storage=storage)

        # 만료된 리포트 조회 시 예외 발생
        from app.services.report_service import ReportExpiredError
        with pytest.raises(ReportExpiredError):
            await service.get_report(expired_report.id)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

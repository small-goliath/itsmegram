"""
Analytics Service 테스트
분석 트래킹 및 통계 계산 기능 테스트
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List

from app.services.analytics_service import (
    AnalyticsService,
    AnalyticsEvent,
    EventType,
    analytics_service,
)


@pytest.fixture
def analytics():
    """테스트용 AnalyticsService 인스턴스"""
    return AnalyticsService(max_events=1000)


@pytest.fixture
def sample_username():
    """테스트용 사용자명"""
    return "testuser123"


@pytest.fixture
def sample_ip():
    """테스트용 IP 주소"""
    return "192.168.1.100"


@pytest.fixture
def sample_report_id():
    """테스트용 리포트 ID"""
    return "test_report_123"


class TestAnalyticsService:
    """AnalyticsService 기본 기능 테스트"""

    @pytest.mark.asyncio
    async def test_track_event(self, analytics):
        """범용 이벤트 트래킹 테스트"""
        event = await analytics.track_event(
            event_type=EventType.PAGE_VIEW,
            session_id="session_123",
            metadata={"page": "/home"},
        )

        assert event.event_type == EventType.PAGE_VIEW
        assert event.session_id == "session_123"
        assert event.metadata["page"] == "/home"
        assert event.timestamp is not None

    @pytest.mark.asyncio
    async def test_track_page_view(self, analytics, sample_ip):
        """페이지 조회 트래킹 테스트"""
        event = await analytics.track_page_view(
            page="/analyze",
            session_id="session_456",
            ip_address=sample_ip,
        )

        assert event.event_type == EventType.PAGE_VIEW
        assert event.metadata["page"] == "/analyze"
        assert event.hashed_ip is not None
        # IP가 해시되었는지 확인 (원본 IP와 다름)
        assert event.hashed_ip != sample_ip

    @pytest.mark.asyncio
    async def test_track_analysis_start(self, analytics, sample_username, sample_ip, sample_report_id):
        """분석 시작 트래킹 테스트"""
        event = await analytics.track_analysis_start(
            report_id=sample_report_id,
            username=sample_username,
            session_id="session_789",
            ip_address=sample_ip,
        )

        assert event.event_type == EventType.ANALYSIS_START
        assert event.report_id == sample_report_id
        assert event.hashed_username is not None
        # 사용자명이 해시되었는지 확인
        assert event.hashed_username != sample_username
        # 시작 시간이 기록되었는지 확인
        assert sample_report_id in analytics._analysis_start_times

    @pytest.mark.asyncio
    async def test_track_analysis_complete(self, analytics, sample_username, sample_report_id):
        """분석 완료 트래킹 테스트"""
        # 먼저 시작 이벤트를 생성
        await analytics.track_analysis_start(
            report_id=sample_report_id,
            username=sample_username,
        )

        # 완료 이벤트 생성
        event = await analytics.track_analysis_complete(
            report_id=sample_report_id,
            username=sample_username,
            metadata={"posts_count": 20},
        )

        assert event.event_type == EventType.ANALYSIS_COMPLETE
        assert event.report_id == sample_report_id
        assert event.duration_ms is not None
        assert event.duration_ms >= 0
        assert event.metadata["posts_count"] == 20
        # 시작 시간이 제거되었는지 확인
        assert sample_report_id not in analytics._analysis_start_times

    @pytest.mark.asyncio
    async def test_track_analysis_failed(self, analytics, sample_username, sample_report_id):
        """분석 실패 트래킹 테스트"""
        # 먼저 시작 이벤트를 생성
        await analytics.track_analysis_start(
            report_id=sample_report_id,
            username=sample_username,
        )

        # 실패 이벤트 생성
        event = await analytics.track_analysis_failed(
            report_id=sample_report_id,
            username=sample_username,
            error_message="Profile not found",
        )

        assert event.event_type == EventType.ANALYSIS_FAILED
        assert event.report_id == sample_report_id
        assert event.duration_ms is not None
        assert event.metadata["error"] == "Profile not found"

    @pytest.mark.asyncio
    async def test_track_share(self, analytics, sample_report_id, sample_username):
        """공유 트래킹 테스트"""
        event = await analytics.track_share(
            report_id=sample_report_id,
            platform="instagram",
            username=sample_username,
        )

        assert event.event_type == EventType.SHARE
        assert event.report_id == sample_report_id
        assert event.metadata["platform"] == "instagram"

    @pytest.mark.asyncio
    async def test_track_download(self, analytics, sample_report_id, sample_username):
        """다운로드 트래킹 테스트"""
        event = await analytics.track_download(
            report_id=sample_report_id,
            format="png",
            username=sample_username,
        )

        assert event.event_type == EventType.DOWNLOAD
        assert event.report_id == sample_report_id
        assert event.metadata["format"] == "png"


class TestStatisticsCalculation:
    """통계 계산 테스트"""

    @pytest.mark.asyncio
    async def test_get_completion_rate(self, analytics):
        """완료율 계산 테스트"""
        # 5개 완료, 2개 실패
        for i in range(5):
            await analytics.track_analysis_complete(
                report_id=f"report_complete_{i}",
                username=f"user_{i}",
            )

        for i in range(2):
            await analytics.track_analysis_failed(
                report_id=f"report_failed_{i}",
                username=f"fail_user_{i}",
            )

        completion_rate = analytics.get_completion_rate()

        # 완료율 = 5 / (5 + 2) = 0.714...
        assert completion_rate == pytest.approx(5 / 7, rel=1e-3)

    @pytest.mark.asyncio
    async def test_get_completion_rate_no_data(self, analytics):
        """데이터 없을 때 완료율 테스트"""
        completion_rate = analytics.get_completion_rate()
        assert completion_rate == 0.0

    @pytest.mark.asyncio
    async def test_get_avg_duration(self, analytics):
        """평균 소요시간 계산 테스트"""
        # 완료 이벤트 생성 (소요 시간 포함)
        event1 = AnalyticsEvent(
            event_type=EventType.ANALYSIS_COMPLETE,
            duration_ms=1000,
        )
        event2 = AnalyticsEvent(
            event_type=EventType.ANALYSIS_COMPLETE,
            duration_ms=2000,
        )
        event3 = AnalyticsEvent(
            event_type=EventType.ANALYSIS_COMPLETE,
            duration_ms=3000,
        )

        analytics._events = [event1, event2, event3]

        avg_duration = analytics.get_avg_duration()

        # 평균 = (1000 + 2000 + 3000) / 3 = 2000
        assert avg_duration == pytest.approx(2000.0, rel=1e-3)

    @pytest.mark.asyncio
    async def test_get_avg_duration_no_data(self, analytics):
        """데이터 없을 때 평균 소요시간 테스트"""
        avg_duration = analytics.get_avg_duration()
        assert avg_duration is None

    @pytest.mark.asyncio
    async def test_get_share_rate(self, analytics):
        """공유율 계산 테스트"""
        # 10개 완료, 3개 공유
        for i in range(10):
            await analytics.track_analysis_complete(
                report_id=f"report_{i}",
                username=f"user_{i}",
            )

        for i in range(3):
            await analytics.track_share(
                report_id=f"report_{i}",
                platform="instagram",
                username=f"user_{i}",
            )

        share_rate = analytics.get_share_rate()

        # 공유율 = 3 / 10 = 0.3
        assert share_rate == pytest.approx(0.3, rel=1e-3)

    @pytest.mark.asyncio
    async def test_get_share_rate_no_completed(self, analytics):
        """완료된 분석 없을 때 공유율 테스트"""
        share_rate = analytics.get_share_rate()
        assert share_rate == 0.0

    @pytest.mark.asyncio
    async def test_get_stats(self, analytics):
        """전체 통계 조회 테스트"""
        # 다양한 이벤트 생성
        await analytics.track_page_view(page="/home")
        await analytics.track_analysis_start(report_id="r1", username="user1")
        await analytics.track_analysis_complete(report_id="r1", username="user1")
        await analytics.track_share(report_id="r1", platform="instagram")
        await analytics.track_download(report_id="r1", format="png")

        stats = analytics.get_stats()

        assert stats["total_events"] == 5
        assert stats["event_counts"]["page_view"] == 1
        assert stats["event_counts"]["analysis_start"] == 1
        assert stats["event_counts"]["analysis_complete"] == 1
        assert stats["event_counts"]["share"] == 1
        assert stats["event_counts"]["download"] == 1
        assert stats["unique_users"] == 1
        assert stats["completion_rate"] == 1.0
        assert stats["share_rate"] == 1.0


class TestTimeRangeFiltering:
    """시간 범위 필터링 테스트"""

    @pytest.mark.asyncio
    async def test_get_events_in_range(self, analytics):
        """시간 범위로 이벤트 필터링 테스트"""
        now = datetime.utcnow()

        # 과거 이벤트
        old_event = AnalyticsEvent(
            event_type=EventType.PAGE_VIEW,
            timestamp=now - timedelta(days=10),
        )

        # 최근 이벤트
        recent_event = AnalyticsEvent(
            event_type=EventType.PAGE_VIEW,
            timestamp=now - timedelta(days=1),
        )

        analytics._events = [old_event, recent_event]

        # 최근 7일 이벤트 조회
        week_ago = now - timedelta(days=7)
        events = analytics._get_events_in_range(start_time=week_ago, end_time=now)

        assert len(events) == 1
        assert events[0].timestamp == recent_event.timestamp

    @pytest.mark.asyncio
    async def test_get_stats_with_time_range(self, analytics):
        """시간 범위로 통계 조회 테스트"""
        now = datetime.utcnow()

        # 과거 완료 이벤트
        old_event = AnalyticsEvent(
            event_type=EventType.ANALYSIS_COMPLETE,
            timestamp=now - timedelta(days=10),
        )

        # 최근 완료 이벤트
        recent_event = AnalyticsEvent(
            event_type=EventType.ANALYSIS_COMPLETE,
            timestamp=now - timedelta(days=1),
        )

        analytics._events = [old_event, recent_event]

        # 전체 기간 통계
        all_stats = analytics.get_stats()
        assert all_stats["total_events"] == 2

        # 최근 7일 통계
        week_ago = now - timedelta(days=7)
        week_stats = analytics.get_stats(start_time=week_ago, end_time=now)
        assert week_stats["total_events"] == 1


class TestDataPrivacy:
    """개인정보 보호 테스트"""

    def test_username_hashing(self, analytics):
        """사용자명 해시화 테스트"""
        username = "testuser"
        hashed = analytics._hash_username(username)

        # 해시 값이 원본과 다름
        assert hashed != username
        # 해시 값이 비어있지 않음
        assert len(hashed) > 0
        # 동일한 입력은 동일한 해시 값
        assert analytics._hash_username(username) == hashed
        # 다른 입력은 다른 해시 값
        assert analytics._hash_username("otheruser") != hashed

    def test_ip_hashing(self, analytics):
        """IP 주소 해시화 테스트"""
        ip = "192.168.1.1"
        hashed = analytics._hash_ip(ip)

        # 해시 값이 원본과 다름
        assert hashed != ip
        # 해시 값이 비어있지 않음
        assert len(hashed) > 0
        # 동일한 입력은 동일한 해시 값
        assert analytics._hash_ip(ip) == hashed
        # 다른 입력은 다른 해시 값
        assert analytics._hash_ip("192.168.1.2") != hashed

    @pytest.mark.asyncio
    async def test_sensitive_data_not_stored_raw(self, analytics, sample_username, sample_ip):
        """민감한 데이터가 원본으로 저장되지 않는지 테스트"""
        await analytics.track_analysis_start(
            report_id="test_report",
            username=sample_username,
            ip_address=sample_ip,
        )

        event = analytics._events[0]

        # 원본이 저장되지 않았는지 확인
        assert event.hashed_username != sample_username
        assert event.hashed_ip != sample_ip


class TestDashboardData:
    """대시보드 데이터 테스트"""

    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, analytics):
        """대시보드 데이터 조회 테스트"""
        # 다양한 이벤트 생성
        await analytics.track_analysis_start(report_id="r1", username="user1")
        await analytics.track_analysis_complete(report_id="r1", username="user1")
        await analytics.track_share(report_id="r1", platform="instagram")
        await analytics.track_download(report_id="r1", format="png")

        dashboard = analytics.get_dashboard_data()

        assert "summary" in dashboard
        assert "periods" in dashboard
        assert "breakdown" in dashboard
        assert "generated_at" in dashboard

        # summary 확인
        summary = dashboard["summary"]
        assert summary["total_events"] == 4
        assert summary["total_analyses"] == 1
        assert summary["completed_analyses"] == 1
        assert summary["total_shares"] == 1
        assert summary["total_downloads"] == 1

        # periods 확인
        periods = dashboard["periods"]
        assert "today" in periods
        assert "last_7_days" in periods
        assert "last_30_days" in periods
        assert "all_time" in periods

        # breakdown 확인
        breakdown = dashboard["breakdown"]
        assert "platform_shares" in breakdown
        assert "format_downloads" in breakdown


class TestEventHandlers:
    """이벤트 핸들러 테스트"""

    @pytest.mark.asyncio
    async def test_register_event_handler(self, analytics):
        """이벤트 핸들러 등록 테스트"""
        handler_called = False
        received_event = None

        def test_handler(event):
            nonlocal handler_called, received_event
            handler_called = True
            received_event = event

        analytics.register_event_handler(test_handler)

        await analytics.track_event(event_type=EventType.PAGE_VIEW)

        assert handler_called is True
        assert received_event is not None
        assert received_event.event_type == EventType.PAGE_VIEW


class TestEventStorage:
    """이벤트 저장소 테스트"""

    def test_max_events_limit(self):
        """최대 이벤트 수 제한 테스트"""
        analytics = AnalyticsService(max_events=5)

        # 10개 이벤트 추가
        for i in range(10):
            event = AnalyticsEvent(
                event_type=EventType.PAGE_VIEW,
                timestamp=datetime.utcnow() + timedelta(seconds=i),
            )
            analytics._add_event(event)

        # 최대 5개만 유지
        assert len(analytics._events) == 5
        # 가장 최근 이벤트만 남아있음
        assert analytics._events[0].timestamp < analytics._events[-1].timestamp

    @pytest.mark.asyncio
    async def test_clear_old_events(self, analytics):
        """오래된 이벤트 정리 테스트"""
        now = datetime.utcnow()

        # 오래된 이벤트
        old_event = AnalyticsEvent(
            event_type=EventType.PAGE_VIEW,
            timestamp=now - timedelta(days=40),
        )

        # 최근 이벤트
        recent_event = AnalyticsEvent(
            event_type=EventType.PAGE_VIEW,
            timestamp=now - timedelta(days=5),
        )

        analytics._events = [old_event, recent_event]

        # 30일 이상 된 이벤트 정리
        removed = analytics.clear_old_events(days=30)

        assert removed == 1
        assert len(analytics._events) == 1
        assert analytics._events[0].timestamp == recent_event.timestamp


class TestEventToDict:
    """이벤트 직렬화 테스트"""

    def test_event_to_dict(self):
        """이벤트를 딕셔너리로 변환 테스트"""
        now = datetime.utcnow()
        event = AnalyticsEvent(
            event_type=EventType.ANALYSIS_COMPLETE,
            timestamp=now,
            session_id="session_123",
            hashed_username="hashed_user_123",
            hashed_ip="hashed_ip_123",
            report_id="report_123",
            metadata={"key": "value"},
            duration_ms=1500,
        )

        data = event.to_dict()

        assert data["event_type"] == "analysis_complete"
        assert data["timestamp"] == now.isoformat()
        assert data["session_id"] == "session_123"
        assert data["hashed_username"] == "hashed_user_123"
        assert data["hashed_ip"] == "hashed_ip_123"
        assert data["report_id"] == "report_123"
        assert data["metadata"] == {"key": "value"}
        assert data["duration_ms"] == 1500


class TestSingletonInstance:
    """싱글톤 인스턴스 테스트"""

    def test_analytics_service_singleton(self):
        """AnalyticsService 싱글톤 인스턴스 존재 확인"""
        assert analytics_service is not None
        assert isinstance(analytics_service, AnalyticsService)

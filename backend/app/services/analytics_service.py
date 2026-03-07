"""
itsmegram - Analytics Service
분석 완료율 트래킹 및 통계 계산 서비스

개인정보 보호를 위해 username과 IP 주소는 해시하여 저장됩니다.
"""

import hashlib
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict

import structlog

from app.config import get_settings

logger = structlog.get_logger()


class EventType(str, Enum):
    """이벤트 타입 열거형"""
    PAGE_VIEW = "page_view"
    ANALYSIS_START = "analysis_start"
    ANALYSIS_COMPLETE = "analysis_complete"
    ANALYSIS_FAILED = "analysis_failed"
    SHARE = "share"
    DOWNLOAD = "download"


@dataclass
class AnalyticsEvent:
    """분석 이벤트 데이터 클래스"""
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    hashed_username: Optional[str] = None
    hashed_ip: Optional[str] = None
    report_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[int] = None  # 분석 소요 시간 (밀리초)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "hashed_username": self.hashed_username,
            "hashed_ip": self.hashed_ip,
            "report_id": self.report_id,
            "metadata": self.metadata,
            "duration_ms": self.duration_ms,
        }


class AnalyticsService:
    """
    분석 트래킹 및 통계 서비스

    - 이벤트 트래킹 (page_view, analysis_start, analysis_complete, etc.)
    - 통계 계산 (완료율, 평균 소요시간, 공유율 등)
    - 개인정보 보호를 위한 데이터 해시화
    """

    def __init__(self, max_events: int = 10000):
        self._events: List[AnalyticsEvent] = []
        self._max_events = max_events
        self._analysis_start_times: Dict[str, datetime] = {}  # report_id -> start_time
        self._lock = asyncio.Lock()
        self._event_handlers: List[Callable[[AnalyticsEvent], None]] = []

        logger.info("analytics_service_initialized", max_events=max_events)

    def _hash_username(self, username: str) -> str:
        """
        사용자명을 SHA-256으로 해시하여 익명화

        Args:
            username: 원본 사용자명

        Returns:
            해시된 사용자명 (hex 문자열)
        """
        if not username:
            return ""
        return hashlib.sha256(username.lower().encode()).hexdigest()[:32]

    def _hash_ip(self, ip_address: str) -> str:
        """
        IP 주소를 SHA-256으로 해시하여 익명화

        Args:
            ip_address: 원본 IP 주소

        Returns:
            해시된 IP 주소 (hex 문자열)
        """
        if not ip_address:
            return ""
        return hashlib.sha256(ip_address.encode()).hexdigest()[:32]

    def _add_event(self, event: AnalyticsEvent) -> None:
        """이벤트 추가 (날짜별 순환 버퍼)"""
        self._events.append(event)

        # 최대 이벤트 수 제한 (오래된 것부터 삭제)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

        # 이벤트 핸들러 호출
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error("event_handler_error", error=str(e))

        # 로그 기록 (개인정보 보호를 위해 해시된 값만)
        logger.info(
            "analytics_event_recorded",
            event_type=event.event_type.value,
            hashed_username=event.hashed_username,
            report_id=event.report_id,
        )

    def register_event_handler(self, handler: Callable[[AnalyticsEvent], None]) -> None:
        """
        이벤트 핸들러 등록

        Args:
            handler: 이벤트 발생 시 호출될 콜백 함수
        """
        self._event_handlers.append(handler)
        logger.info("event_handler_registered", handler_name=handler.__name__)

    # ========== 이벤트 트래킹 메서드 ==========

    async def track_event(
        self,
        event_type: EventType,
        session_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        report_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[int] = None,
    ) -> AnalyticsEvent:
        """
        범용 이벤트 트래킹

        Args:
            event_type: 이벤트 타입
            session_id: 세션 ID
            username: 사용자명 (해시되어 저장됨)
            ip_address: IP 주소 (해시되어 저장됨)
            report_id: 리포트 ID
            metadata: 추가 메타데이터
            duration_ms: 소요 시간 (밀리초)

        Returns:
            생성된 AnalyticsEvent
        """
        async with self._lock:
            event = AnalyticsEvent(
                event_type=event_type,
                session_id=session_id,
                hashed_username=self._hash_username(username) if username else None,
                hashed_ip=self._hash_ip(ip_address) if ip_address else None,
                report_id=report_id,
                metadata=metadata or {},
                duration_ms=duration_ms,
            )
            self._add_event(event)
            return event

    async def track_page_view(
        self,
        page: str,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnalyticsEvent:
        """
        페이지 조회 트래킹

        Args:
            page: 페이지 경로
            session_id: 세션 ID
            ip_address: IP 주소 (해시되어 저장됨)
            metadata: 추가 메타데이터

        Returns:
            생성된 AnalyticsEvent
        """
        meta = metadata or {}
        meta["page"] = page

        return await self.track_event(
            event_type=EventType.PAGE_VIEW,
            session_id=session_id,
            ip_address=ip_address,
            metadata=meta,
        )

    async def track_analysis_start(
        self,
        report_id: str,
        username: str,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnalyticsEvent:
        """
        분석 시작 트래킹

        Args:
            report_id: 리포트 ID
            username: 사용자명 (해시되어 저장됨)
            session_id: 세션 ID
            ip_address: IP 주소 (해시되어 저장됨)
            metadata: 추가 메타데이터

        Returns:
            생성된 AnalyticsEvent
        """
        async with self._lock:
            # 시작 시간 기록
            self._analysis_start_times[report_id] = datetime.utcnow()

            event = AnalyticsEvent(
                event_type=EventType.ANALYSIS_START,
                session_id=session_id,
                hashed_username=self._hash_username(username),
                hashed_ip=self._hash_ip(ip_address) if ip_address else None,
                report_id=report_id,
                metadata=metadata or {},
            )
            self._add_event(event)
            return event

    async def track_analysis_complete(
        self,
        report_id: str,
        username: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnalyticsEvent:
        """
        분석 완료 트래킹

        Args:
            report_id: 리포트 ID
            username: 사용자명 (해시되어 저장됨)
            metadata: 추가 메타데이터

        Returns:
            생성된 AnalyticsEvent
        """
        async with self._lock:
            # 소요 시간 계산
            duration_ms = None
            start_time = self._analysis_start_times.pop(report_id, None)
            if start_time:
                duration = datetime.utcnow() - start_time
                duration_ms = int(duration.total_seconds() * 1000)

            event = AnalyticsEvent(
                event_type=EventType.ANALYSIS_COMPLETE,
                hashed_username=self._hash_username(username),
                report_id=report_id,
                metadata=metadata or {},
                duration_ms=duration_ms,
            )
            self._add_event(event)
            return event

    async def track_analysis_failed(
        self,
        report_id: str,
        username: str,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnalyticsEvent:
        """
        분석 실패 트래킹

        Args:
            report_id: 리포트 ID
            username: 사용자명 (해시되어 저장됨)
            error_message: 에러 메시지
            metadata: 추가 메타데이터

        Returns:
            생성된 AnalyticsEvent
        """
        async with self._lock:
            # 소요 시간 계산
            duration_ms = None
            start_time = self._analysis_start_times.pop(report_id, None)
            if start_time:
                duration = datetime.utcnow() - start_time
                duration_ms = int(duration.total_seconds() * 1000)

            meta = metadata or {}
            if error_message:
                meta["error"] = error_message

            event = AnalyticsEvent(
                event_type=EventType.ANALYSIS_FAILED,
                hashed_username=self._hash_username(username),
                report_id=report_id,
                metadata=meta,
                duration_ms=duration_ms,
            )
            self._add_event(event)
            return event

    async def track_share(
        self,
        report_id: str,
        platform: str,
        username: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnalyticsEvent:
        """
        공유 트래킹

        Args:
            report_id: 리포트 ID
            platform: 공유 플랫폼 (instagram, twitter, facebook, native, etc.)
            username: 사용자명 (해시되어 저장됨)
            metadata: 추가 메타데이터

        Returns:
            생성된 AnalyticsEvent
        """
        meta = metadata or {}
        meta["platform"] = platform

        return await self.track_event(
            event_type=EventType.SHARE,
            report_id=report_id,
            username=username,
            metadata=meta,
        )

    async def track_download(
        self,
        report_id: str,
        format: str,
        username: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnalyticsEvent:
        """
        다운로드 트래킹

        Args:
            report_id: 리포트 ID
            format: 다운로드 형식 (png, jpg, pdf, etc.)
            username: 사용자명 (해시되어 저장됨)
            metadata: 추가 메타데이터

        Returns:
            생성된 AnalyticsEvent
        """
        meta = metadata or {}
        meta["format"] = format

        return await self.track_event(
            event_type=EventType.DOWNLOAD,
            report_id=report_id,
            username=username,
            metadata=meta,
        )

    # ========== 통계 계산 메서드 ==========

    def _get_events_in_range(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[EventType] = None,
    ) -> List[AnalyticsEvent]:
        """
        시간 범위와 이벤트 타입으로 이벤트 필터링

        Args:
            start_time: 시작 시간
            end_time: 종료 시간
            event_type: 이벤트 타입

        Returns:
            필터링된 이벤트 목록
        """
        events = self._events

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]
        if end_time:
            events = [e for e in events if e.timestamp <= end_time]
        if event_type:
            events = [e for e in events if e.event_type == event_type]

        return events

    def get_stats(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        전체 통계 조회

        Args:
            start_time: 시작 시간 (None이면 전체)
            end_time: 종료 시간 (None이면 전체)

        Returns:
            통계 데이터 딕셔너리
        """
        events = self._get_events_in_range(start_time, end_time)

        # 이벤트 타입별 카운트
        event_counts = defaultdict(int)
        for event in events:
            event_counts[event.event_type.value] += 1

        # 고유 사용자 수 (해시된 username 기준)
        unique_users = len(set(
            e.hashed_username for e in events
            if e.hashed_username
        ))

        # 고유 세션 수
        unique_sessions = len(set(
            e.session_id for e in events
            if e.session_id
        ))

        # 시간 범위
        if events:
            time_range_start = min(e.timestamp for e in events)
            time_range_end = max(e.timestamp for e in events)
        else:
            time_range_start = None
            time_range_end = None

        return {
            "total_events": len(events),
            "event_counts": dict(event_counts),
            "unique_users": unique_users,
            "unique_sessions": unique_sessions,
            "time_range": {
                "start": time_range_start.isoformat() if time_range_start else None,
                "end": time_range_end.isoformat() if time_range_end else None,
            },
            "completion_rate": self.get_completion_rate(start_time, end_time),
            "avg_duration_ms": self.get_avg_duration(start_time, end_time),
            "share_rate": self.get_share_rate(start_time, end_time),
        }

    def get_completion_rate(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> float:
        """
        분석 완료율 계산

        완료율 = 완료된 분석 수 / (완료된 분석 수 + 실패한 분석 수)

        Args:
            start_time: 시작 시간
            end_time: 종료 시간

        Returns:
            완료율 (0.0 ~ 1.0)
        """
        events = self._get_events_in_range(start_time, end_time)

        completed = sum(1 for e in events if e.event_type == EventType.ANALYSIS_COMPLETE)
        failed = sum(1 for e in events if e.event_type == EventType.ANALYSIS_FAILED)
        total = completed + failed

        if total == 0:
            return 0.0

        return completed / total

    def get_avg_duration(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Optional[float]:
        """
        평균 분석 소요시간 계산 (밀리초)

        Args:
            start_time: 시작 시간
            end_time: 종료 시간

        Returns:
            평균 소요시간 (밀리초) 또는 None (데이터 없음)
        """
        events = self._get_events_in_range(start_time, end_time)

        durations = [
            e.duration_ms for e in events
            if e.duration_ms is not None and
            e.event_type in (EventType.ANALYSIS_COMPLETE, EventType.ANALYSIS_FAILED)
        ]

        if not durations:
            return None

        return sum(durations) / len(durations)

    def get_share_rate(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> float:
        """
        공유율 계산

        공유율 = 공유 횟수 / 완료된 분석 수

        Args:
            start_time: 시작 시간
            end_time: 종료 시간

        Returns:
            공유율 (0.0 ~ 1.0)
        """
        events = self._get_events_in_range(start_time, end_time)

        shares = sum(1 for e in events if e.event_type == EventType.SHARE)
        completed = sum(1 for e in events if e.event_type == EventType.ANALYSIS_COMPLETE)

        if completed == 0:
            return 0.0

        return shares / completed

    def get_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_type: Optional[EventType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        이벤트 로그 조회

        Args:
            start_time: 시작 시간
            end_time: 종료 시간
            event_type: 이벤트 타입 필터
            limit: 최대 조회 개수
            offset: 오프셋

        Returns:
            이벤트 딕셔너리 목록
        """
        events = self._get_events_in_range(start_time, end_time, event_type)

        # 최신순 정렬
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)

        # 페이징
        paginated = events[offset:offset + limit]

        return [e.to_dict() for e in paginated]

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        대시보드용 통계 데이터 조회

        Returns:
            대시보드 데이터 딕셔너리
        """
        now = datetime.utcnow()

        # 오늘 통계
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_stats = self.get_stats(today_start, now)

        # 최근 7일 통계
        week_start = now - timedelta(days=7)
        week_stats = self.get_stats(week_start, now)

        # 최근 30일 통계
        month_start = now - timedelta(days=30)
        month_stats = self.get_stats(month_start, now)

        # 전체 통계
        all_stats = self.get_stats()

        # 플랫폼별 공유 통계
        share_events = self._get_events_in_range(event_type=EventType.SHARE)
        platform_shares = defaultdict(int)
        for event in share_events:
            platform = event.metadata.get("platform", "unknown")
            platform_shares[platform] += 1

        # 다운로드 형식별 통계
        download_events = self._get_events_in_range(event_type=EventType.DOWNLOAD)
        format_downloads = defaultdict(int)
        for event in download_events:
            format_type = event.metadata.get("format", "unknown")
            format_downloads[format_type] += 1

        return {
            "summary": {
                "total_events": all_stats["total_events"],
                "total_analyses": all_stats["event_counts"].get("analysis_start", 0),
                "completed_analyses": all_stats["event_counts"].get("analysis_complete", 0),
                "failed_analyses": all_stats["event_counts"].get("analysis_failed", 0),
                "total_shares": all_stats["event_counts"].get("share", 0),
                "total_downloads": all_stats["event_counts"].get("download", 0),
                "unique_users": all_stats["unique_users"],
                "completion_rate": all_stats["completion_rate"],
                "avg_duration_ms": all_stats["avg_duration_ms"],
                "share_rate": all_stats["share_rate"],
            },
            "periods": {
                "today": today_stats,
                "last_7_days": week_stats,
                "last_30_days": month_stats,
                "all_time": all_stats,
            },
            "breakdown": {
                "platform_shares": dict(platform_shares),
                "format_downloads": dict(format_downloads),
            },
            "generated_at": now.isoformat(),
        }

    def clear_old_events(self, days: int = 30) -> int:
        """
        오래된 이벤트 정리

        Args:
            days: 보관할 일수

        Returns:
            삭제된 이벤트 수
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        original_count = len(self._events)

        self._events = [e for e in self._events if e.timestamp >= cutoff]
        removed_count = original_count - len(self._events)

        logger.info("old_events_cleared", removed_count=removed_count, cutoff_days=days)
        return removed_count


# 싱글톤 인스턴스
analytics_service = AnalyticsService()
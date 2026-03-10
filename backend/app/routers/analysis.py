"""
AI 분석 라우터
인스타그램 계정 AI 분석 API
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request, BackgroundTasks
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnalysisStatus,
    InstagramProfile,
    AnalysisMetrics,
    AIInsight,
    ReportData,
    ErrorResponse,
    InstagramData,
)
from app.config import get_settings
from app.services.instagram_service import instagram_service
from app.services.ai_service import ai_service
from app.services.queue_manager import queue_manager, QueueStatus
from app.utils.exceptions import (
    AIServiceError,
    MoonshotAPIError,
    AnalysisTimeoutError,
)
from app.services.report_service import report_service, ReportCreationError
from app.services.analytics_service import analytics_service
from app.utils.logger import get_logger
import structlog

logger = get_logger("analysis_router")
struct_logger = structlog.get_logger()

router = APIRouter()

# Rate Limiter 인스턴스 (main.py에서 주입됨)
limiter = Limiter(key_func=get_remote_address)


async def _process_analysis(report_id: str) -> dict:
    """
    실제 분석 처리 함수 (큐에서 실행)
    """
    from app.services.report_service import report_service

    # 리포트 가져오기
    report = report_service.storage.get(report_id)
    if not report:
        raise ValueError(f"Report {report_id} not found")

    username = report.username

    try:
        struct_logger.info("analysis_started_from_queue", report_id=report_id, username=username)

        # 인스타그램 데이터 수집
        instagram_data = await instagram_service.fetch_full_data(
            username=username,
            posts_limit=20,
            use_cache=True,
        )

        # AI 분석 수행
        report_data = await ai_service.generate_report(instagram_data)

        # 리포트 저장 (storage에 직접 저장)
        from app.services.report_service import report_service
        from app.models.report import ReportStatus

        report = report_service.storage.get(report_id)
        if report:
            report.status = ReportStatus.COMPLETED
            report.report_data = report_data
            report.completed_at = datetime.utcnow()
            report_service.storage.save(report)

        struct_logger.info("analysis_completed_from_queue", report_id=report_id, username=username)
        return {"report_id": report_id, "status": "completed"}

    except Exception as e:
        struct_logger.error("analysis_failed_from_queue", report_id=report_id, username=username, error=str(e))

        # 실패 상태 저장
        from app.models.report import ReportStatus

        if report:
            report.status = ReportStatus.FAILED
            report.error_message = str(e)
            report.completed_at = datetime.utcnow()
            report_service.storage.save(report)

        raise


@router.on_event("startup")
async def startup_event():
    """Start queue processor on app startup"""
    await queue_manager.start()
    struct_logger.info("queue_processor_started")


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        429: {"description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="인스타그램 계정 분석 시작",
    description="인스타그램 사용자명을 받아 AI 분석을 시작합니다. 새로운 리포트 저장소 시스템을 사용합니다.",
)
@limiter.limit("5/hour")  # 분석 요청: IP당 5회/시간
async def start_analysis(
    request: Request,  # slowapi를 위한 Request 객체
    data: AnalyzeRequest,
    background_tasks: BackgroundTasks,
) -> AnalyzeResponse:
    """
    인스타그램 계정 분석을 시작합니다.
    - 큐가 필요한 경우: job_id 반환
    - 큐가 필요 없는 경우: 즉시 처리

    Args:
        request: 분석 요청 (username 포함)

    Returns:
        AnalyzeResponse: 분석 작업 ID와 상태

    Example:
        ```json
        {
            "username": "instagram"
        }
        ```
    """
    settings = get_settings()

    struct_logger.info(
        "analysis_request_received",
        username=data.username,
        client_ip=request.client.host if request.client else None
    )

    try:
        # 큐가 필요한 상황인지 판단
        if queue_manager.should_queue():
            # 리포트 먼저 생성 (pending 상태)
            from app.models.report import Report

            report = Report(
                username=data.username,
                status="pending",
            )
            report_id = report.id

            # storage에 저장
            from app.services.report_service import report_service
            report_service.storage.save(report)

            # 큐에 등록
            job_id = await queue_manager.enqueue(
                username=data.username,
                task_func=_process_analysis,
                report_id=report_id,
            )

            if not job_id:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Server is busy. Please try again later."
                )

            struct_logger.info(
                "analysis_queued",
                report_id=report_id,
                job_id=job_id,
                username=data.username,
                queue_position=queue_manager.get_status(job_id)["queue_position"]
            )

            # 분석 시작 트래킹
            await analytics_service.track_analysis_start(
                report_id=report_id,
                username=data.username,
                session_id=None,
                ip_address=request.client.host if request.client else None,
            )

            return AnalyzeResponse(
                report_id=report_id,
                status=AnalysisStatus.PROCESSING,
                message=f"분석이 대기열에 추가되었습니다. (대기순번: {queue_manager.get_status(job_id)['queue_position']}번)",
                estimated_time_seconds=int(queue_manager.get_status(job_id)["estimated_wait_seconds"]),
                check_url=f"{settings.api_v1_prefix}/queue/{job_id}/status",
            )

        # 즉시 처리
        report_id = await report_service.create_report_async(
            username=data.username,
            background_tasks=background_tasks
        )

        struct_logger.info("analysis_started_immediately", report_id=report_id, username=data.username)

        # 분석 시작 트래킹
        await analytics_service.track_analysis_start(
            report_id=report_id,
            username=data.username,
            session_id=None,
            ip_address=request.client.host if request.client else None,
        )

        return AnalyzeResponse(
            report_id=report_id,
            status=AnalysisStatus.PROCESSING,
            message="분석이 시작되었습니다. 잠시 후 결과를 확인해주세요.",
            estimated_time_seconds=30,
            check_url=f"{settings.api_v1_prefix}/report/{report_id}",
        )

    except ReportCreationError as e:
        struct_logger.error("report_creation_failed", username=data.username, error=e.message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start analysis: {e.message}",
        )

    except Exception as e:
        struct_logger.error("unexpected_analysis_error", username=data.username, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )


@router.get(
    "/analyze/status/{report_id}",
    summary="분석 상태 조회",
    description="특정 분석 작업의 현재 상태를 조회합니다. (레거시 - /report/{report_id}/status 사용 권장)",
    responses={
        404: {"model": ErrorResponse, "description": "Analysis job not found"},
    },
)
async def get_analysis_status(report_id: str) -> dict:
    """
    분석 작업의 상태를 조회합니다.
    새로운 리포트 서비스를 통해 상태를 조회합니다.

    Args:
        report_id: 분석 작업 ID

    Returns:
        dict: 분석 상태 정보
    """
    try:
        # 새로운 리포트 서비스를 통해 상태 조회
        status_info = await report_service.get_report_status(report_id)

        # 레거시 형식으로 변환
        return {
            "report_id": status_info["report_id"],
            "status": status_info["status"],
            "username": status_info.get("username", ""),
            "progress": _get_progress_from_status(status_info["status"]),
            "message": _get_message_from_status(status_info["status"], status_info.get("error_message")),
            "created_at": status_info.get("created_at", ""),
            "expires_at": status_info.get("expires_at", ""),
            "is_expired": status_info.get("is_expired", False),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analysis status: {str(e)}",
        )


def _get_progress_from_status(status: str) -> int:
    """상태에 따른 진행률 반환"""
    progress_map = {
        "processing": 50,
        "completed": 100,
        "failed": 0,
        "not_found": 0,
        "expired": 0,
    }
    return progress_map.get(status, 0)


def _get_message_from_status(status: str, error_message: Optional[str] = None) -> str:
    """상태에 따른 메시지 반환"""
    message_map = {
        "processing": "분석 진행 중...",
        "completed": "분석이 완료되었습니다.",
        "failed": error_message or "분석에 실패했습니다.",
        "not_found": "리포트를 찾을 수 없습니다.",
        "expired": "리포트가 만료되었습니다.",
    }
    return message_map.get(status, "상태를 확인할 수 없습니다.")


@router.post(
    "/analyze/mock/{username}",
    summary="Mock 분석 결과 (테스트용)",
    description="테스트를 위한 Mock 분석 결과를 즉시 반환합니다.",
)
async def mock_analysis(username: str) -> ReportData:
    """
    테스트용 Mock 분석 결과를 반환합니다.

    Args:
        username: 인스타그램 사용자명

    Returns:
        ReportData: Mock 분석 결과
    """
    profile = InstagramProfile(
        username=username.lower(),
        full_name=f"{username.title()} User",
        biography=f"Welcome to {username}'s profile!",
        followers_count=15000,
        following_count=500,
        posts_count=250,
        is_private=False,
        is_verified=False,
    )

    metrics = AnalysisMetrics(
        engagement_rate=3.5,
        avg_likes=525,
        avg_comments=42,
        posting_frequency="weekly",
        best_posting_time="18:00 - 20:00",
        top_hashtags=["#lifestyle", "#travel", "#photography"],
        content_themes=["여행", "일상", "사진"],
    )

    insights = [
        AIInsight(
            category="engagement",
            title="참여도 분석",
            description="팔로워 대비 참여도가 평균 이상입니다. 스토리 기능을 더 활용하면 참여도를 높일 수 있습니다.",
            score=7,
            recommendations=["스토리 게시 빈도 증가", "인터랙티브 스티커 활용"],
        ),
        AIInsight(
            category="content",
            title="콘텐츠 전략",
            description="사진 품질이 우수하며, 일관된 색감으로 브랜드 아이덴티티가 잘 드러납니다.",
            score=8,
            recommendations=["릴스 콘텐츠 추가", "게시 시간 다양화"],
        ),
        AIInsight(
            category="growth",
            title="성장 잠재력",
            description="꾸준한 성장세를 보이고 있으며, 해시태그 전략이 효과적입니다.",
            score=6,
            recommendations=["협업 게시물 증가", "타겟 해시태그 확대"],
        ),
    ]

    return ReportData(
        profile=profile,
        metrics=metrics,
        recent_posts=[],
        ai_insights=insights,
        overall_score=72,
        generated_at=datetime.utcnow(),
    )

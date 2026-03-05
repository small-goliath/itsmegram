"""
AI 분석 라우터
인스타그램 계정 AI 분석 API
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status, Depends, Request
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
)
from app.config import get_settings

router = APIRouter()

# In-memory storage for demo (production에서는 Redis 사용 권장)
analysis_jobs = {}


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
    description="인스타그램 사용자명을 받아 AI 분석을 시작합니다.",
)
async def start_analysis(
    request: AnalyzeRequest,
) -> AnalyzeResponse:
    """
    인스타그램 계정 분석을 시작합니다.

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

    # 고유한 리포트 ID 생성
    report_id = f"rep_{uuid.uuid4().hex[:12]}"

    # 분석 작업 저장 (실제로는 백그라운드 작업 큐에 추가)
    analysis_jobs[report_id] = {
        "username": request.username,
        "status": AnalysisStatus.PROCESSING,
        "created_at": datetime.utcnow(),
        "progress": 0,
    }

    # TODO: 실제 백그라운드 분석 작업 시작
    # Celery, RQ, 또는 FastAPI BackgroundTasks 사용

    return AnalyzeResponse(
        report_id=report_id,
        status=AnalysisStatus.PROCESSING,
        message="분석이 시작되었습니다. 잠시 후 결과를 확인해주세요.",
        estimated_time_seconds=30,
        check_url=f"{settings.api_v1_prefix}/report/{report_id}",
    )


@router.get(
    "/analyze/status/{report_id}",
    summary="분석 상태 조회",
    description="특정 분석 작업의 현재 상태를 조회합니다.",
)
async def get_analysis_status(report_id: str) -> dict:
    """
    분석 작업의 상태를 조회합니다.

    Args:
        report_id: 분석 작업 ID

    Returns:
        dict: 분석 상태 정보
    """
    if report_id not in analysis_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job '{report_id}' not found",
        )

    job = analysis_jobs[report_id]
    return {
        "report_id": report_id,
        "status": job["status"],
        "username": job["username"],
        "progress": job.get("progress", 0),
        "created_at": job["created_at"].isoformat(),
    }


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
        biography=f"Welcome to {username}'s profile! 🌟",
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

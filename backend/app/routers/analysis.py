"""
AI 분석 라우터
인스타그램 계정 AI 분석 API
"""

import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any
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
from app.services.ai_service import ai_service, AIServiceError, MoonshotAPIError, AnalysisTimeoutError

router = APIRouter()

# In-memory storage for demo (production에서는 Redis 사용 권장)
analysis_jobs: Dict[str, Dict[str, Any]] = {}


async def _run_analysis_background(report_id: str, username: str):
    """
    백그라운드에서 AI 분석 수행
    """
    try:
        analysis_jobs[report_id]["progress"] = 10
        analysis_jobs[report_id]["message"] = "인스타그램 데이터 수집 중..."

        # 인스타그램 데이터 수집
        instagram_data = await instagram_service.fetch_full_data(
            username=username,
            posts_limit=20,
            use_cache=True,
        )

        analysis_jobs[report_id]["progress"] = 40
        analysis_jobs[report_id]["message"] = "AI 분석 중..."

        # AI 분석 수행
        report_data = await ai_service.generate_report(instagram_data)

        analysis_jobs[report_id]["progress"] = 100
        analysis_jobs[report_id]["status"] = AnalysisStatus.COMPLETED
        analysis_jobs[report_id]["message"] = "분석이 완료되었습니다."
        analysis_jobs[report_id]["result"] = report_data.model_dump()
        analysis_jobs[report_id]["completed_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        analysis_jobs[report_id]["status"] = AnalysisStatus.FAILED
        analysis_jobs[report_id]["message"] = f"분석 실패: {str(e)}"
        analysis_jobs[report_id]["error"] = str(e)
        analysis_jobs[report_id]["completed_at"] = datetime.utcnow().isoformat()


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
    description="인스타그램 사용자명을 받아 AI 분석을 시작합니다. Moonshot AI를 사용하여 계정을 분석합니다.",
)
async def start_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
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

    # 분석 작업 저장
    analysis_jobs[report_id] = {
        "username": request.username,
        "status": AnalysisStatus.PROCESSING,
        "created_at": datetime.utcnow(),
        "progress": 0,
        "message": "분석 대기 중...",
    }

    # 백그라운드 작업 시작
    background_tasks.add_task(_run_analysis_background, report_id, request.username)

    return AnalyzeResponse(
        report_id=report_id,
        status=AnalysisStatus.PROCESSING,
        message="분석이 시작되었습니다. 잠시 후 결과를 확인해주세요.",
        estimated_time_seconds=30,
        check_url=f"{settings.api_v1_prefix}/analyze/status/{report_id}",
    )


@router.get(
    "/analyze/status/{report_id}",
    summary="분석 상태 조회",
    description="특정 분석 작업의 현재 상태를 조회합니다.",
    responses={
        404: {"model": ErrorResponse, "description": "Analysis job not found"},
    },
)
async def get_analysis_status(report_id: str) -> dict:
    """
    분석 작업의 상태를 조회합니다.

    Args:
        report_id: 분석 작업 ID

    Returns:
        dict: 분석 상태 정보 (status, progress, message, result 등 포함)
    """
    if report_id not in analysis_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis job '{report_id}' not found",
        )

    job = analysis_jobs[report_id]
    response = {
        "report_id": report_id,
        "status": job["status"],
        "username": job["username"],
        "progress": job.get("progress", 0),
        "message": job.get("message", ""),
        "created_at": job["created_at"].isoformat(),
    }

    # 완료된 경우 결과 포함
    if job["status"] == AnalysisStatus.COMPLETED and "result" in job:
        response["result"] = job["result"]
        response["completed_at"] = job.get("completed_at")

    # 실패한 경우 에러 정보 포함
    if job["status"] == AnalysisStatus.FAILED:
        response["error"] = job.get("error", "Unknown error")
        response["completed_at"] = job.get("completed_at")

    return response


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

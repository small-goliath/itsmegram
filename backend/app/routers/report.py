"""
리포트 생성 라우터
분석 리포트 조회 및 관리 API
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    ReportResponse,
    ReportData,
    AnalysisStatus,
    InstagramProfile,
    AnalysisMetrics,
    AIInsight,
    ErrorResponse,
)
from app.config import get_settings

router = APIRouter()

# In-memory report storage (production에서는 Redis/DB 사용)
reports_db = {}


@router.get(
    "/report/{report_id}",
    response_model=ReportResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Report not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="분석 리포트 조회",
    description="특정 리포트 ID로 완성된 분석 리포트를 조회합니다.",
)
async def get_report(report_id: str) -> ReportResponse:
    """
    완성된 분석 리포트를 조회합니다.

    Args:
        report_id: 리포트 고유 ID

    Returns:
        ReportResponse: 완성된 리포트 데이터

    Raises:
        HTTPException: 리포트를 찾을 수 없는 경우
    """
    settings = get_settings()

    # TODO: 실제 DB에서 리포트 조회
    # 현재는 mock 데이터 또는 analysis 라우터의 작업 상태 확인
    from app.routers.analysis import analysis_jobs

    if report_id not in analysis_jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found",
        )

    job = analysis_jobs[report_id]

    # Mock 완료된 리포트 데이터 생성
    profile = InstagramProfile(
        username=job["username"],
        full_name=f"{job['username'].title()} User",
        biography=f"Welcome to {job['username']}'s profile!",
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
            description="팔로워 대비 참여도가 평균 이상입니다.",
            score=7,
            recommendations=["스토리 활용 증가", "인터랙티브 기능 사용"],
        ),
        AIInsight(
            category="content",
            title="콘텐츠 전략",
            description="일관된 톤앤매너로 브랜드 아이덴티티가 뚜렷합니다.",
            score=8,
            recommendations=["릴스 콘텐츠 추가", "게시 시간 최적화"],
        ),
    ]

    report_data = ReportData(
        profile=profile,
        metrics=metrics,
        recent_posts=[],
        ai_insights=insights,
        overall_score=72,
        generated_at=datetime.utcnow(),
    )

    return ReportResponse(
        report_id=report_id,
        username=job["username"],
        status=AnalysisStatus.COMPLETED,
        report_data=report_data,
        image_url=None,  # TODO: 리포트 이미지 생성 후 URL 설정
        created_at=job["created_at"],
        expires_at=job["created_at"] + timedelta(hours=settings.report_ttl_hours),
    )


@router.get(
    "/report/{report_id}/image",
    summary="리포트 이미지 조회",
    description="생성된 리포트 이미지 URL을 조회합니다.",
)
async def get_report_image(report_id: str) -> dict:
    """
    리포트 이미지 URL을 조회합니다.

    Args:
        report_id: 리포트 ID

    Returns:
        dict: 이미지 URL 정보
    """
    # TODO: 실제 이미지 생성 및 URL 반환
    return {
        "report_id": report_id,
        "image_url": None,
        "status": "not_generated",
        "message": "Image generation not implemented yet",
    }


@router.delete(
    "/report/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="리포트 삭제",
    description="특정 리포트를 삭제합니다.",
)
async def delete_report(report_id: str):
    """
    리포트를 삭제합니다.

    Args:
        report_id: 삭제할 리포트 ID
    """
    from app.routers.analysis import analysis_jobs

    if report_id in analysis_jobs:
        del analysis_jobs[report_id]

    if report_id in reports_db:
        del reports_db[report_id]

    return None


@router.get(
    "/reports",
    summary="리포트 목록 조회",
    description="모든 리포트 목록을 조회합니다 (테스트용).",
)
async def list_reports() -> dict:
    """
    저장된 모든 리포트 목록을 조회합니다.

    Returns:
        dict: 리포트 목록
    """
    from app.routers.analysis import analysis_jobs

    return {
        "reports": [
            {
                "report_id": rid,
                "username": job["username"],
                "status": job["status"],
                "created_at": job["created_at"].isoformat(),
            }
            for rid, job in analysis_jobs.items()
        ],
        "total_count": len(analysis_jobs),
    }

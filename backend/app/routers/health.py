"""
Health check router
서버 상태 확인을 위한 라우터
"""

from fastapi import APIRouter, status
from datetime import datetime

from app.models.schemas import HealthResponse
from app.config import get_settings

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="헬스체크",
    description="서버의 기본적인 건강 상태를 확인합니다.",
)
async def health_check() -> HealthResponse:
    """
    서버 건강 상태 확인 엔드포인트

    Returns:
        HealthResponse: 서버 상태 정보
    """
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        service="itsmegram-backend",
        version=settings.app_version,
    )


@router.get(
    "/health/detailed",
    summary="상세 헬스체크",
    description="서버 및 의존성의 상세 상태를 확인합니다.",
)
async def detailed_health_check() -> dict:
    """
    상세 서버 상태 확인 엔드포인트
    TODO: 데이터베이스 연결, 외부 API 상태 등 추가
    """
    settings = get_settings()
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "itsmegram-backend",
        "version": settings.app_version,
        "environment": "development" if settings.debug else "production",
        "checks": {
            "api": "ok",
            "config": "ok",
            # "database": "ok",  # TODO: DB 연결 후 추가
            # "redis": "ok",  # TODO: Redis 연결 후 추가
            # "moonshot_api": "ok",  # TODO: Moonshot API 연결 후 추가
        },
    }

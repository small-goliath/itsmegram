"""
Health check router
서버 상태 확인을 위한 라우터
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    서버 건강 상태 확인 엔드포인트
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "itsmegram-backend",
    }


@router.get("/health/detailed")
async def detailed_health_check():
    """
    상세 서버 상태 확인 엔드포인트
    TODO: 데이터베이스 연결, 외부 API 상태 등 추가
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "itsmegram-backend",
        "version": "0.1.0",
        "checks": {
            "api": "ok",
            # "database": "ok",  # TODO: DB 연결 후 추가
            # "moonshot_api": "ok",  # TODO: Moonshot API 연결 후 추가
        },
    }

"""
itsmegram - Instagram AI Analyzer Backend
FastAPI 애플리케이션 진입점
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging

from app.config import get_settings
from app.routers import health, instagram, analysis, report
from app.models.schemas import ErrorResponse

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rate Limiter 설정
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 수명 주기 관리
    - 시작 시: 데이터베이스 연결, 캐시 초기화 등
    - 종료 시: 리소스 정리
    """
    # Startup
    settings = get_settings()
    logger.info(f"🚀 itsmegram backend starting... (version: {settings.app_version})")
    yield
    # Shutdown
    logger.info("👋 itsmegram backend shutting down...")


# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="itsmegram API",
    description="Instagram AI Analyzer - 인스타그램 계정을 AI로 분석하는 서비스",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate Limiter 상태 설정
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 설정 로드
settings = get_settings()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 글로벌 에러 핸들러
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """ValueError 핸들러"""
    logger.warning(f"ValueError: {str(exc)} - Path: {request.url.path}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="Bad Request",
            detail=str(exc),
            code="VALIDATION_ERROR"
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    logger.error(f"Unhandled exception: {str(exc)} - Path: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred",
            code="INTERNAL_ERROR"
        ).model_dump(),
    )


# API v1 라우터 등록
API_V1_PREFIX = settings.api_v1_prefix

app.include_router(health.router, prefix=API_V1_PREFIX, tags=["health"])
app.include_router(instagram.router, prefix=API_V1_PREFIX, tags=["instagram"])
app.include_router(analysis.router, prefix=API_V1_PREFIX, tags=["analysis"])
app.include_router(report.router, prefix=API_V1_PREFIX, tags=["report"])


@app.get("/")
async def root():
    """루트 엔드포인트 - 서비스 상태 확인"""
    return {
        "message": "Welcome to itsmegram API",
        "version": settings.app_version,
        "docs": "/docs",
        "api_prefix": API_V1_PREFIX,
    }


@app.get("/api")
async def api_root():
    """API 루트 엔드포인트 (하위 호환성)"""
    return {
        "message": "itsmegram API",
        "version": settings.app_version,
        "endpoints": {
            "health": f"{API_V1_PREFIX}/health",
            "analyze": f"{API_V1_PREFIX}/analyze",
            "report": f"{API_V1_PREFIX}/report/{{report_id}}",
            "docs": "/docs",
        },
    }

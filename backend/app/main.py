"""
itsmegram - Instagram AI Analyzer Backend
FastAPI 애플리케이션 진입점
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.routers import health, instagram, analysis, report
from app.utils.logger import setup_logging, get_logger
from app.middleware.error_handler import setup_exception_handlers

# 설정 로드
settings = get_settings()

# 구조화된 로깅 설정
setup_logging(
    level=settings.log_level if hasattr(settings, "log_level") else "INFO",
    json_format=not settings.debug,  # 개발 환경에서는 콘솔 출력, 프로덕션에서는 JSON
)

logger = get_logger(__name__)

# Rate Limiter 설정 - 전역 기본 제한: 100/minute
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 수명 주기 관리
    - 시작 시: 데이터베이스 연결, 캐시 초기화 등
    - 종료 시: 리소스 정리
    """
    # Startup
    logger.info(
        "application_starting",
        version=settings.app_version,
        debug=settings.debug,
        environment="development" if settings.debug else "production"
    )
    yield
    # Shutdown
    logger.info("application_shutting_down")


# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="itsmegram API",
    description="Instagram AI Analyzer - 인스타그램 계정을 AI로 분석하는 서비스",
    version=settings.app_version,
    lifespan=lifespan,
)

# Rate Limiter 상태 설정
app.state.limiter = limiter

# 글로벌 예외 핸들러 등록
setup_exception_handlers(app)

# 커스텀 Rate Limit 초과 에러 핸들러 (SlowAPI)
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Rate Limit 초과 시 커스텀 응답"""
    logger.warning(
        "rate_limit_exceeded",
        path=request.url.path,
        client_ip=get_remote_address(request)
    )
    return JSONResponse(
        status_code=429,
        content={
            "error": "RATE_LIMITED",
            "message": "너무 많은 요청이 발생했습니다. 잠시 후 다시 시도해주세요.",
            "suggestion": "분석 요청은 시간당 5회로 제한됩니다. 잠시 후 다시 시도해주세요.",
            "retry_after": 3600,
            "limit": "5/hour"
        },
        headers={"Retry-After": "3600"}
    )

# CORS 설정 강화
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # 필요한 메서드만 허용
    allow_headers=["*"],
    max_age=600,  # preflight 캐시 10분
)

# 신뢰할 수 있는 호스트만 허용 (프로덕션)
if not settings.debug:
    allowed_hosts = settings.allowed_hosts_list
    if "*" not in allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=allowed_hosts
        )
        logger.info("trusted_host_middleware_enabled", allowed_hosts=allowed_hosts)

# GZip 압축 미들웨어 추가 (1KB 이상 응답만 압축)
app.add_middleware(GZipMiddleware, minimum_size=1000)
logger.info("gzip_middleware_enabled", minimum_size=1000)


# API v1 라우터 등록
API_V1_PREFIX = settings.api_v1_prefix

app.include_router(health.router, prefix=API_V1_PREFIX, tags=["health"])
app.include_router(instagram.router, prefix=API_V1_PREFIX, tags=["instagram"])
app.include_router(analysis.router, prefix=API_V1_PREFIX, tags=["analysis"])
app.include_router(report.router, prefix=API_V1_PREFIX, tags=["report"])

logger.info(
    "routers_registered",
    routers=["health", "instagram", "analysis", "report"],
    prefix=API_V1_PREFIX
)


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

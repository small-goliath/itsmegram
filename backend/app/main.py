"""
itsmegram - Instagram AI Analyzer Backend
FastAPI 애플리케이션 진입점
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.routers import health


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 수명 주기 관리
    - 시작 시: 데이터베이스 연결, 캐시 초기화 등
    - 종료 시: 리소스 정리
    """
    # Startup
    print("🚀 itsmegram backend starting...")
    yield
    # Shutdown
    print("👋 itsmegram backend shutting down...")


# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="itsmegram API",
    description="Instagram AI Analyzer - 인스타그램 계정을 AI로 분석하는 서비스",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 설정
# 환경 변수에서 허용된 오리진 목록을 가져옴 (쉼표로 구분)
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(health.router, prefix="/api", tags=["health"])


@app.get("/")
async def root():
    """루트 엔드포인트 - 서비스 상태 확인"""
    return {
        "message": "Welcome to itsmegram API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/api")
async def api_root():
    """API 루트 엔드포인트"""
    return {
        "message": "itsmegram API",
        "version": "0.1.0",
        "endpoints": {
            "health": "/api/health",
            "docs": "/docs",
        },
    }

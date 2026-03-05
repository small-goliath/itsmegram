"""
itsmegram - Pydantic 모델 정의
API 요청/응답에 사용되는 데이터 모델
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class AnalysisStatus(str, Enum):
    """분석 상태 열거형"""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalyzeRequest(BaseModel):
    """
    분석 요청 모델
    인스타그램 계정 분석을 위한 요청 데이터
    """
    username: str = Field(
        ...,
        description="분석할 인스타그램 사용자명 (username)",
        examples=["instagram", "natgeo"],
        min_length=1,
        max_length=30,
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """
        인스타그램 사용자명 유효성 검사
        - 영문자, 숫자, 밑줄(_), 마침표(.)만 허용
        - 공백 불가
        """
        import re
        if not re.match(r'^[a-zA-Z0-9._]{1,30}$', v):
            raise ValueError(
                "사용자명은 1-30자의 영문자, 숫자, 밑줄(_), 마침표(.)만 사용 가능합니다"
            )
        return v.lower().strip()  # 소문자로 변환 및 공백 제거

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "instagram"
            }
        }
    }


class AnalyzeResponse(BaseModel):
    """
    분석 응답 모델
    분석 요청에 대한 응답 데이터
    """
    report_id: str = Field(
        ...,
        description="생성된 리포트 고유 ID",
        examples=["rep_abc123def456"],
    )
    status: AnalysisStatus = Field(
        ...,
        description="분석 상태 (processing/completed/failed)",
        examples=["processing"],
    )
    message: str = Field(
        default="분석이 시작되었습니다",
        description="상태 메시지",
    )
    estimated_time_seconds: int = Field(
        default=30,
        description="예상 완료 시간(초)",
        ge=0,
    )
    check_url: Optional[str] = Field(
        default=None,
        description="리포트 조회 URL",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "report_id": "rep_abc123def456",
                "status": "processing",
                "message": "분석이 시작되었습니다",
                "estimated_time_seconds": 30,
                "check_url": "/api/v1/report/rep_abc123def456"
            }
        }
    }


class InstagramProfile(BaseModel):
    """인스타그램 프로필 정보"""
    username: str
    full_name: Optional[str] = None
    biography: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    profile_pic_url: Optional[str] = None
    is_private: bool = False
    is_verified: bool = False
    external_url: Optional[str] = None


class PostAnalysis(BaseModel):
    """게시물 분석 결과"""
    post_id: str
    caption: Optional[str] = None
    likes_count: int = 0
    comments_count: int = 0
    timestamp: Optional[datetime] = None
    media_type: Optional[str] = None  # image, video, carousel
    hashtags: List[str] = Field(default_factory=list)
    mentions: List[str] = Field(default_factory=list)


class AnalysisMetrics(BaseModel):
    """분석 메트릭스"""
    engagement_rate: float = Field(0.0, ge=0.0, le=100.0)
    avg_likes: float = 0.0
    avg_comments: float = 0.0
    posting_frequency: Optional[str] = None  # daily, weekly, monthly
    best_posting_time: Optional[str] = None
    top_hashtags: List[str] = Field(default_factory=list)
    content_themes: List[str] = Field(default_factory=list)


class AIInsight(BaseModel):
    """AI 분석 인사이트"""
    category: str = Field(..., description="인사이트 카테고리 (e.g., content, engagement, growth)")
    title: str = Field(..., description="인사이트 제목")
    description: str = Field(..., description="상세 설명")
    score: Optional[int] = Field(None, ge=1, le=10, description="점수 (1-10)")
    recommendations: List[str] = Field(default_factory=list)


class ReportData(BaseModel):
    """리포트 데이터 모델"""
    profile: InstagramProfile
    metrics: AnalysisMetrics
    recent_posts: List[PostAnalysis] = Field(default_factory=list)
    ai_insights: List[AIInsight] = Field(default_factory=list)
    overall_score: Optional[int] = Field(None, ge=1, le=100)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ReportResponse(BaseModel):
    """
    리포트 응답 모델
    완성된 분석 리포트 데이터
    """
    report_id: str = Field(..., description="리포트 고유 ID")
    username: str = Field(..., description="분석된 사용자명")
    status: AnalysisStatus = Field(..., description="리포트 상태")
    report_data: ReportData = Field(..., description="상세 분석 데이터")
    image_url: Optional[str] = Field(None, description="생성된 리포트 이미지 URL")
    created_at: datetime = Field(..., description="생성 시간")
    expires_at: Optional[datetime] = Field(None, description="만료 시간")

    model_config = {
        "json_schema_extra": {
            "example": {
                "report_id": "rep_abc123def456",
                "username": "instagram",
                "status": "completed",
                "report_data": {
                    "profile": {
                        "username": "instagram",
                        "full_name": "Instagram",
                        "followers_count": 1000000,
                        "following_count": 100,
                        "posts_count": 5000,
                        "is_verified": True,
                    },
                    "metrics": {
                        "engagement_rate": 3.5,
                        "avg_likes": 50000,
                        "avg_comments": 1000,
                    },
                    "ai_insights": [],
                    "overall_score": 85,
                    "generated_at": "2024-01-01T00:00:00Z"
                },
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    }


class HealthResponse(BaseModel):
    """헬스체크 응답 모델"""
    status: str
    timestamp: datetime
    service: str
    version: str


class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

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
        pattern=r'^[a-zA-Z0-9._]+$',
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """
        인스타그램 사용자명 유효성 검사
        - 영문자, 숫자, 밑줄(_), 마침표(.)만 허용
        - 공백 불가
        - 예약된 사용자명 체크
        - 연속된 특수문자 체크
        """
        import re

        # 기본 패턴 검사
        if not re.match(r'^[a-zA-Z0-9._]{1,30}$', v):
            raise ValueError(
                "사용자명은 1-30자의 영문자, 숫자, 밑줄(_), 마침표(.)만 사용 가능합니다"
            )

        # 예약된 사용자명 체크
        reserved = ['admin', 'api', 'report', 'marketing', 'health', 'docs', 'static', 'media']
        if v.lower() in reserved:
            raise ValueError('사용할 수 없는 사용자명입니다')

        # 연속된 점/언더스코어 체크
        if '..' in v or '__' in v:
            raise ValueError('잘못된 사용자명 형식입니다')

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


# ========== Instagram 데이터 수집 모델 ==========

class ProfileData(BaseModel):
    """인스타그램 프로필 데이터 모델"""
    username: str = Field(..., description="사용자명")
    full_name: str = Field(default="", description="전체 이름")
    biography: str = Field(default="", description="소개글")
    followers: int = Field(default=0, description="팔로워 수")
    following: int = Field(default=0, description="팔로잉 수")
    posts_count: int = Field(default=0, description="게시물 수")
    is_private: bool = Field(default=False, description="비공개 계정 여부")
    profile_pic_url: str = Field(default="", description="프로필 사진 URL")
    is_verified: bool = Field(default=False, description="인증된 계정 여부")
    external_url: Optional[str] = Field(default=None, description="외부 링크")


class PostData(BaseModel):
    """인스타그램 게시물 데이터 모델"""
    post_id: str = Field(..., description="게시물 ID")
    caption: str = Field(default="", description="캡션")
    likes: int = Field(default=0, description="좋아요 수")
    comments: int = Field(default=0, description="댓글 수")
    media_url: str = Field(default="", description="미디어 URL")
    hashtags: List[str] = Field(default_factory=list, description="해시태그 목록")
    mentions: List[str] = Field(default_factory=list, description="멘션 목록")
    timestamp: Optional[datetime] = Field(default=None, description="게시 시간")
    post_type: str = Field(default="image", description="게시물 타입 (image, video, carousel)")
    shortcode: str = Field(default="", description="게시물 shortcode")


class InstagramData(BaseModel):
    """수집된 인스타그램 전체 데이터 모델"""
    profile: ProfileData = Field(..., description="프로필 정보")
    posts: List[PostData] = Field(default_factory=list, description="게시물 목록")
    collected_at: datetime = Field(default_factory=datetime.utcnow, description="수집 시간")


class ProfileResponse(BaseModel):
    """프로필 조회 응답 모델"""
    success: bool = Field(default=True, description="성공 여부")
    data: ProfileData = Field(..., description="프로필 데이터")
    cached: bool = Field(default=False, description="캐시된 데이터 여부")


class PostsResponse(BaseModel):
    """게시물 조회 응답 모델"""
    success: bool = Field(default=True, description="성공 여부")
    username: str = Field(..., description="사용자명")
    posts: List[PostData] = Field(default_factory=list, description="게시물 목록")
    total_count: int = Field(default=0, description="총 게시물 수")
    fetched_count: int = Field(default=0, description="가져온 게시물 수")
    cached: bool = Field(default=False, description="캐시된 데이터 여부")


class ValidationResponse(BaseModel):
    """사용자명 검증 응답 모델"""
    username: str = Field(..., description="사용자명")
    is_valid: bool = Field(..., description="유효성 여부")
    exists: Optional[bool] = Field(default=None, description="계정 존재 여부")
    is_private: Optional[bool] = Field(default=None, description="비공개 계정 여부")
    message: str = Field(default="", description="메시지")

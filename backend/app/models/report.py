"""
itsmegram - 리포트 데이터 모델
Redis 저장을 위한 리포트 데이터 구조 정의
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ReportSection(BaseModel):
    """리포트 섹션 모델"""
    title: str = Field(..., description="섹션 제목")
    icon: str = Field(..., description="섹션 아이콘")
    content: Dict[str, Any] = Field(..., description="섹션 내용")


class Report(BaseModel):
    """
    분석 리포트 모델
    Redis에 저장되는 완전한 리포트 데이터 구조
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="리포트 고유 ID")
    username: str = Field(..., description="분석된 인스타그램 사용자명")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=168),
        description="만료 시간 (기본 7일)"
    )

    # 리포트 섹션들 (AI 분석 결과)
    basic_metrics: Dict[str, Any] = Field(default_factory=dict, description="기본 메트릭스")
    content_tendency: Dict[str, Any] = Field(default_factory=dict, description="콘텐츠 성향")
    lifestyle: Dict[str, Any] = Field(default_factory=dict, description="라이프스타일")
    personality: Dict[str, Any] = Field(default_factory=dict, description="성격 분석")
    network: Dict[str, Any] = Field(default_factory=dict, description="네트워크 분석")
    growth_potential: Dict[str, Any] = Field(default_factory=dict, description="성장 잠재력")
    summary: str = Field(default="", description="종합 요약")

    # 메타데이터
    profile_image_url: str = Field(default="", description="프로필 이미지 URL")
    profile_image_base64: str = Field(default="", description="프로필 이미지 base64 data URI (이미지 생성용)")
    collected_posts_count: int = Field(default=0, description="수집된 게시물 수")
    status: str = Field(default="processing", description="리포트 상태 (processing, completed, failed)")
    error_message: Optional[str] = Field(default=None, description="에러 메시지 (실패 시)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "instagram",
                "created_at": "2024-01-01T00:00:00Z",
                "expires_at": "2024-01-02T00:00:00Z",
                "basic_metrics": {
                    "avg_likes": 75.5,
                    "engagement_rate": 60.0,
                    "post_type_ratio": {"image": 0.6, "video": 0.3, "carousel": 0.1}
                },
                "content_tendency": {
                    "categories": ["여행", "일상"],
                    "visual_style": "밝고 선명한 색감의 스타일로 보입니다",
                    "text_style": "친근하고 자연스러운 문체를 사용하는 것으로 추정됩니다",
                    "hashtag_pattern": ["브랜드 해시태그", "일상 태그"]
                },
                "lifestyle": {
                    "interests": ["여행", "사진", "음식"],
                    "activity_pattern": "주말에 활동이 집중되는 패턴으로 보입니다",
                    "consumption": ["체험 중심 소비", "가성비 중시"]
                },
                "personality": {
                    "extroversion": "외향적인 성향으로 보입니다",
                    "expression_strength": 80.0,
                    "communication": "친근하고 개방적인 커뮤니케이션 스타일로 보입니다"
                },
                "network": {
                    "engagement_quality": "높은 참여 품질을 보이는 것으로 추정됩니다",
                    "community_type": "관심사 기반 커뮤니티로 보입니다"
                },
                "growth_potential": {
                    "trend": "안정적인 성장 추세로 보입니다",
                    "consistency": "꾸준한 활동을 유지하는 것으로 추정됩니다",
                    "suggestions": ["릴스 콘텐츠 강화", "게시 시간 최적화"]
                },
                "summary": "이 계정은 여행과 일상 콘텐츠를 중심으로 활동하는 것으로 보입니다...",
                "profile_image_url": "https://example.com/profile.jpg",
                "collected_posts_count": 20,
                "status": "completed",
                "error_message": None
            }
        }
    }

    def is_expired(self) -> bool:
        """리포트가 만료되었는지 확인"""
        return datetime.utcnow() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return self.model_dump()

    def to_json(self) -> str:
        """JSON 문자열로 변환"""
        return self.model_dump_json()

"""
itsmegram - 설정 관리 모듈
Pydantic Settings를 사용한 환경 변수 관리
"""

from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """
    애플리케이션 설정 클래스
    환경 변수에서 자동으로 값을 로드합니다.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # 정의되지 않은 환경 변수 무시
    )

    # 앱 설정
    app_name: str = "itsmegram"
    app_version: str = "0.1.0"
    debug: bool = False

    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000

    # Moonshot AI API 설정
    moonshot_api_key: str = ""

    # Instagram API 설정 (선택적)
    instagram_api_token: Optional[str] = None
    instagram_app_id: Optional[str] = None
    instagram_app_secret: Optional[str] = None

    # CORS 설정
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        """CORS 오리진을 리스트로 반환"""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # Rate Limiting 설정
    rate_limit: str = "5/hour"
    rate_limit_key_prefix: str = "ratelimit"

    # Redis 설정
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False  # 기본적으로 비활성화 (개발 환경)

    # 로깅 설정
    log_level: str = "info"
    log_format: str = "json"  # json 또는 console

    # API 설정
    api_v1_prefix: str = "/api/v1"

    # 리포트 설정
    report_ttl_hours: int = 24  # 리포트 캐시 유효 시간

    # 신뢰할 수 있는 호스트 설정 (프로덕션)
    allowed_hosts: str = "*"

    @property
    def allowed_hosts_list(self) -> List[str]:
        """신뢰할 수 있는 호스트를 리스트로 반환"""
        if self.allowed_hosts == "*":
            return ["*"]
        return [host.strip() for host in self.allowed_hosts.split(",")]

    @field_validator("moonshot_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Moonshot API 키 유효성 검사"""
        if not v or v == "your_moonshot_api_key_here":
            raise ValueError("MOONSHOT_API_KEY가 설정되지 않았습니다")
        return v

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        """CORS 오리진 유효성 검사"""
        if not v:
            return "http://localhost:3000"
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    설정 객체를 싱글톤 패턴으로 반환
    캐싱을 통해 환경 변수를 여러 번 읽지 않도록 합니다.
    """
    return Settings()

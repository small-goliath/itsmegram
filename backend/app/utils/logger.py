"""
itsmegram - 구조화된 로깅 설정
structlog와 표준 라이브러리 logging을 통합하여 사용
"""

import logging
import sys
from typing import Any, Dict, Optional

import structlog
from pythonjsonlogger import jsonlogger


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_file: Optional[str] = None
) -> None:
    """
    구조화된 로깅 설정 초기화

    Args:
        level: 로깅 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: JSON 형식으로 출력할지 여부
        log_file: 로그 파일 경로 (None이면 콘솔만 출력)
    """
    # 표준 라이브러리 logging 설정
    handlers: list = []

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    handlers.append(console_handler)

    # 파일 핸들러 (선택적)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        handlers.append(file_handler)

    # JSON 포맷터 설정
    if json_format:
        formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s %(pathname)s %(lineno)d",
            rename_fields={
                "timestamp": "ts",
                "level": "lvl",
                "name": "logger",
                "pathname": "path",
                "lineno": "line"
            }
        )
        for handler in handlers:
            handler.setFormatter(formatter)

    # 루트 로거 설정
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers,
        format="%(message)s" if json_format else "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # structlog 설정
    shared_processors: list = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_format:
        # JSON 출력용 프로세서
        structlog.configure(
            processors=shared_processors + [structlog.processors.JSONRenderer()],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        # 콘솔 출력용 프로세서 (개발 환경)
        structlog.configure(
            processors=shared_processors + [
                structlog.dev.ConsoleRenderer(colors=True)
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    # 외부 라이브러리 로깅 레벨 조정 (너무 많은 로그 방지)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("instaloader").setLevel(logging.WARNING)

    # 로깅 설정 완료 로그
    logger = structlog.get_logger()
    logger.info(
        "logging_setup_completed",
        level=level,
        json_format=json_format,
        log_file=log_file
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    구조화된 로거 가져오기

    Args:
        name: 로거 이름 (보통 __name__ 사용)

    Returns:
        structlog BoundLogger 인스턴스
    """
    return structlog.get_logger(name)


def sanitize_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    민감한 정보를 마스킹하여 로그에 안전하게 기록

    Args:
        data: 원본 데이터 딕셔너리

    Returns:
        민감한 정보가 마스킹된 데이터 딕셔너리
    """
    sensitive_keys = [
        "password", "api_key", "apikey", "secret_key", "secret",
        "authorization", "cookie", "session",
        "access_token", "refresh_token", "private_key"
    ]
    # 정확히 일치해야 하는 키들
    exact_match_keys = ["credential", "token"]

    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()
        # 부분 문자열 매칭
        is_sensitive = any(s in key_lower for s in sensitive_keys)
        # 정확한 키 매칭
        is_exact_match = key_lower in exact_match_keys

        if is_sensitive or is_exact_match:
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_sensitive_data(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_sensitive_data(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized

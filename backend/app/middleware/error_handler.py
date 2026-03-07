"""
itsmegram - 글로벌 에러 핸들러
모든 예외 상황에 대한 통합 처리 및 사용자 친화적인 에러 응답 제공
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.logger import get_logger
from app.utils.exceptions import (
    InstagramServiceError,
    ProfileNotFoundError,
    PrivateAccountError,
    RateLimitError,
    AIServiceError,
    MoonshotAPIError,
    AnalysisParsingError,
    AnalysisTimeoutError,
    ReportServiceError,
    ReportNotFoundError,
    ReportExpiredError,
    ReportCreationError,
    StorageError,
)

logger = get_logger("error_handler")


# =============================================================================
# 에러 응답 헬퍼 함수
# =============================================================================

def create_error_response(
    error_code: str,
    message: str,
    suggestion: str,
    status_code: int = 500,
    extra: dict = None
) -> JSONResponse:
    """
    표준화된 에러 응답 생성

    Args:
        error_code: 에러 코드 (대문자 스네이크케이스)
        message: 사용자에게 표시할 에러 메시지
        suggestion: 사용자가 취할 수 있는 제안
        status_code: HTTP 상태 코드
        extra: 추가 필드 (선택적)

    Returns:
        JSONResponse: 표준화된 에러 응답
    """
    content = {
        "error": error_code,
        "message": message,
        "suggestion": suggestion
    }
    if extra:
        content.update(extra)
    return JSONResponse(status_code=status_code, content=content)


# =============================================================================
# 에러 핸들러 함수들
# =============================================================================

async def profile_not_found_handler(request: Request, exc: ProfileNotFoundError):
    """프로필을 찾을 수 없을 때 핸들러"""
    logger.warning(
        "profile_not_found",
        username=exc.username,
        path=request.url.path,
        client_ip=request.client.host if request.client else None
    )
    return create_error_response(
        error_code="USER_NOT_FOUND",
        message=f"사용자 '{exc.username}'를 찾을 수 없습니다",
        suggestion="사용자명을 확인하고 다시 시도해주세요",
        status_code=404
    )


async def private_account_handler(request: Request, exc: PrivateAccountError):
    """비공개 계정일 때 핸들러"""
    logger.warning(
        "private_account_access_denied",
        username=exc.username,
        path=request.url.path,
        client_ip=request.client.host if request.client else None
    )
    return create_error_response(
        error_code="PRIVATE_ACCOUNT",
        message="비공개 계정은 분석할 수 없습니다",
        suggestion="계정을 공개로 변경 후 다시 시도해주세요",
        status_code=400
    )


async def rate_limit_handler(request: Request, exc: RateLimitError):
    """Rate Limit 초과 시 핸들러"""
    logger.error(
        "rate_limit_exceeded",
        message=exc.message,
        path=request.url.path,
        client_ip=request.client.host if request.client else None
    )
    return create_error_response(
        error_code="RATE_LIMIT_EXCEEDED",
        message="Instagram API 요청 한도를 초과했습니다",
        suggestion="잠시 후 다시 시도해주세요 (보통 1시간 후 재시도 가능)",
        status_code=429,
        extra={"retry_after": 3600}
    )


async def ai_service_handler(request: Request, exc: AIServiceError):
    """AI 서비스 에러 핸들러"""
    logger.error(
        "ai_service_error",
        error_code=exc.code,
        message=exc.message,
        path=request.url.path
    )
    return create_error_response(
        error_code="AI_SERVICE_ERROR",
        message="AI 분석 서비스에 일시적인 문제가 발생했습니다",
        suggestion="잠시 후 다시 시도해주세요",
        status_code=503
    )


async def analysis_timeout_handler(request: Request, exc: AnalysisTimeoutError):
    """분석 타임아웃 핸들러"""
    logger.error(
        "analysis_timeout",
        timeout_seconds=exc.timeout_seconds,
        path=request.url.path
    )
    return create_error_response(
        error_code="ANALYSIS_TIMEOUT",
        message="AI 분석이 시간 초과되었습니다",
        suggestion="데이터가 너무 많거나 서버가 바쁩니다. 잠시 후 다시 시도해주세요",
        status_code=504
    )


async def analysis_parsing_handler(request: Request, exc: AnalysisParsingError):
    """분석 결과 파싱 에러 핸들러"""
    logger.error(
        "analysis_parsing_error",
        message=exc.message,
        path=request.url.path
    )
    return create_error_response(
        error_code="ANALYSIS_PARSING_ERROR",
        message="AI 분석 결과를 처리하는 중 오류가 발생했습니다",
        suggestion="다시 시도해주세요. 문제가 지속되면 관리자에게 문의해주세요",
        status_code=500
    )


async def report_not_found_handler(request: Request, exc: ReportNotFoundError):
    """리포트를 찾을 수 없을 때 핸들러"""
    logger.warning(
        "report_not_found",
        report_id=exc.report_id,
        path=request.url.path
    )
    return create_error_response(
        error_code="REPORT_NOT_FOUND",
        message="리포트를 찾을 수 없습니다",
        suggestion="분석을 다시 요청해주세요",
        status_code=404
    )


async def report_expired_handler(request: Request, exc: ReportExpiredError):
    """리포트 만료 시 핸들러"""
    logger.info(
        "report_expired",
        report_id=exc.report_id,
        path=request.url.path
    )
    return create_error_response(
        error_code="REPORT_EXPIRED",
        message="리포트가 만료되었습니다 (24시간 경과)",
        suggestion="개인정보 보호를 위해 24시간 후 리포트가 자동 삭제됩니다. 다시 분석해주세요.",
        status_code=410
    )


async def report_creation_handler(request: Request, exc: ReportCreationError):
    """리포트 생성 실패 핸들러"""
    logger.error(
        "report_creation_failed",
        username=exc.username,
        message=exc.message,
        path=request.url.path
    )
    return create_error_response(
        error_code="REPORT_CREATION_FAILED",
        message="리포트 생성에 실패했습니다",
        suggestion="잠시 후 다시 시도해주세요. 문제가 지속되면 다른 사용자명으로 시도필보세요",
        status_code=500
    )


async def storage_error_handler(request: Request, exc: StorageError):
    """저장소 에러 핸들러"""
    logger.error(
        "storage_error",
        error_code=exc.code,
        message=exc.message,
        path=request.url.path
    )
    return create_error_response(
        error_code="STORAGE_ERROR",
        message="데이터 저장/조회 중 오류가 발생했습니다",
        suggestion="잠시 후 다시 시도해주세요",
        status_code=503
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """HTTP 예외 핸들러"""
    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path
    )

    error_code = "HTTP_ERROR"
    message = str(exc.detail)
    suggestion = "요청을 확인하고 다시 시도해주세요"

    if exc.status_code == 404:
        error_code = "NOT_FOUND"
        message = "요청한 리소스를 찾을 수 없습니다"
        suggestion = "URL을 확인하고 다시 시도해주세요"
    elif exc.status_code == 405:
        error_code = "METHOD_NOT_ALLOWED"
        message = "허용되지 않은 HTTP 메서드입니다"
        suggestion = "올바른 HTTP 메서드를 사용해주세요"
    elif exc.status_code == 400:
        error_code = "BAD_REQUEST"
        message = "잘못된 요청입니다"
        suggestion = "요청 파라미터를 확인해주세요"

    return create_error_response(
        error_code=error_code,
        message=message,
        suggestion=suggestion,
        status_code=exc.status_code
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """요청 검증 실패 핸들러"""
    errors = exc.errors()
    logger.warning(
        "validation_error",
        errors=errors,
        path=request.url.path
    )

    # 첫 번째 에러 메시지 추출
    first_error = errors[0] if errors else {}
    field = ".".join(str(x) for x in first_error.get("loc", []))
    msg = first_error.get("msg", "알 수 없는 오류")

    return create_error_response(
        error_code="VALIDATION_ERROR",
        message=f"입력값 검증 실패: {field} - {msg}",
        suggestion="요청 데이터의 형식과 값을 확인해주세요",
        status_code=422,
        extra={"errors": errors} if errors else None
    )


async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러 (최후의 수단)"""
    logger.error(
        "unhandled_exception",
        exception_type=type(exc).__name__,
        message=str(exc),
        path=request.url.path,
        exc_info=True
    )
    return create_error_response(
        error_code="INTERNAL_ERROR",
        message="서버 내부 오류가 발생했습니다",
        suggestion="잠시 후 다시 시도해주세요. 문제가 지속되면 관리자에게 문의해주세요",
        status_code=500
    )


# =============================================================================
# 예외 핸들러 등록 함수
# =============================================================================

def setup_exception_handlers(app: FastAPI) -> None:
    """
    FastAPI 앱에 모든 예외 핸들러 등록

    Args:
        app: FastAPI 애플리케이션 인스턴스
    """
    # Instagram 관련 예외
    app.add_exception_handler(ProfileNotFoundError, profile_not_found_handler)
    app.add_exception_handler(PrivateAccountError, private_account_handler)
    app.add_exception_handler(RateLimitError, rate_limit_handler)

    # AI 분석 관련 예외
    app.add_exception_handler(AIServiceError, ai_service_handler)
    app.add_exception_handler(AnalysisTimeoutError, analysis_timeout_handler)
    app.add_exception_handler(AnalysisParsingError, analysis_parsing_handler)

    # 리포트 관련 예외
    app.add_exception_handler(ReportNotFoundError, report_not_found_handler)
    app.add_exception_handler(ReportExpiredError, report_expired_handler)
    app.add_exception_handler(ReportCreationError, report_creation_handler)

    # 저장소 관련 예외
    app.add_exception_handler(StorageError, storage_error_handler)

    # 표준 예외
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("exception_handlers_registered")

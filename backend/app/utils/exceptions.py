"""
itsmegram - 공통 예외 클래스
모든 예외를 한 곳에서 정의하여 일관된 에러 처리 제공
"""


class AppError(Exception):
    """애플리케이션 기본 예외"""
    def __init__(self, message: str, code: str = "app_error"):
        self.message = message
        self.code = code
        super().__init__(self.message)


# =============================================================================
# Instagram 서비스 예외
# =============================================================================

class InstagramServiceError(AppError):
    """Instagram 서비스 기본 예외"""
    def __init__(self, message: str, code: str = "instagram_error"):
        super().__init__(message=message, code=code)


class ProfileNotFoundError(InstagramServiceError):
    """프로필을 찾을 수 없는 경우"""
    def __init__(self, username: str):
        self.username = username
        super().__init__(
            message=f"Profile '{username}' not found",
            code="profile_not_found"
        )


class PrivateAccountError(InstagramServiceError):
    """비공개 계정인 경우"""
    def __init__(self, username: str):
        self.username = username
        super().__init__(
            message=f"Account '{username}' is private and cannot be analyzed",
            code="private_account"
        )


class RateLimitError(InstagramServiceError):
    """API Rate Limit에 걸린 경우"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            code="rate_limit"
        )


# =============================================================================
# AI 서비스 예외
# =============================================================================

class AIServiceError(AppError):
    """AI 서비스 기본 예외"""
    def __init__(self, message: str, code: str = "ai_error"):
        super().__init__(message=message, code=code)


class MoonshotAPIError(AIServiceError):
    """Moonshot API 호출 오류"""
    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message=message, code="moonshot_api_error")
        self.original_error = original_error


class AnalysisParsingError(AIServiceError):
    """분석 결과 파싱 오류"""
    def __init__(self, message: str, raw_content: str = None):
        super().__init__(message=message, code="analysis_parsing_error")
        self.raw_content = raw_content


class AnalysisTimeoutError(AIServiceError):
    """분석 타임아웃 오류"""
    def __init__(self, timeout_seconds: int = 30):
        super().__init__(
            message=f"Analysis timed out after {timeout_seconds} seconds",
            code="analysis_timeout"
        )
        self.timeout_seconds = timeout_seconds


# =============================================================================
# 리포트 서비스 예외
# =============================================================================

class ReportServiceError(AppError):
    """리포트 서비스 기본 예외"""
    def __init__(self, message: str, code: str = "report_service_error"):
        super().__init__(message=message, code=code)


class ReportNotFoundError(ReportServiceError):
    """리포트를 찾을 수 없는 경우"""
    def __init__(self, report_id: str):
        self.report_id = report_id
        super().__init__(
            message=f"Report '{report_id}' not found",
            code="report_not_found"
        )


class ReportExpiredError(ReportServiceError):
    """리포트가 만료된 경우"""
    def __init__(self, report_id: str):
        self.report_id = report_id
        super().__init__(
            message=f"Report '{report_id}' has expired",
            code="report_expired"
        )


class ReportCreationError(ReportServiceError):
    """리포트 생성 오류"""
    def __init__(self, message: str, username: str = None):
        super().__init__(message=message, code="report_creation_error")
        self.username = username


# =============================================================================
# 저장소 예외
# =============================================================================

class StorageError(AppError):
    """저장소 기본 예외"""
    def __init__(self, message: str, code: str = "storage_error"):
        super().__init__(message=message, code=code)

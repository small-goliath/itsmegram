"""
itsmegram - HTTP 요청/응답 로깅 미들웨어
모든 API 요청과 응답을 로깅하여 디버깅 및 모니터링 지원
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.logger import get_logger

logger = get_logger("request_logger")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    HTTP 요청/응답 로깅 미들웨어

    모든 요청의 메서드, 경로, 처리 시간, 상태 코드를 로깅합니다.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 요청 시작 시간
        start_time = time.time()

        # 클라이언트 정보
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        path = request.url.path
        query_string = str(request.query_params) if request.query_params else ""

        # 요청 바디 (있는 경우, 민감한 정보 제외)
        body = None
        if method in ["POST", "PUT", "PATCH"]:
            try:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    body_bytes = await request.body()
                    if body_bytes:
                        body = body_bytes.decode("utf-8")[:1000]  # 최대 1000자
                        # 민감한 정보 마스킹
                        import re
                        body = re.sub(r'"(password|token|api_key|secret)":\s*"[^"]*"',
                                     r'"\1": "***REDACTED***"', body)
            except Exception:
                pass

        # 요청 로깅
        log_data = {
            "event": "request_started",
            "method": method,
            "path": path,
            "query": query_string,
            "client_ip": client_ip,
            "user_agent": user_agent[:100] if user_agent else "unknown",
        }
        if body:
            log_data["body_preview"] = body[:200] + "..." if len(body) > 200 else body

        logger.info(**log_data)

        try:
            # 요청 처리
            response = await call_next(request)

            # 처리 시간 계산
            process_time = time.time() - start_time

            # 응답 로깅
            logger.info(
                "request_completed",
                method=method,
                path=path,
                status_code=response.status_code,
                process_time_ms=round(process_time * 1000, 2),
                client_ip=client_ip,
            )

            # 응답 헤더에 처리 시간 추가
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            # 에러 발생 시 로깅
            process_time = time.time() - start_time
            logger.error(
                "request_failed",
                method=method,
                path=path,
                error_type=type(e).__name__,
                error_message=str(e),
                process_time_ms=round(process_time * 1000, 2),
                client_ip=client_ip,
                exc_info=True,
            )
            raise


class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """
    에러 로깅 미들웨어
    응답 상태 코드가 400 이상인 경우 상세 로깅
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 에러 응답 로깅 (400 이상)
        if response.status_code >= 400:
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(
                "error_response",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                client_ip=client_ip,
            )

        return response

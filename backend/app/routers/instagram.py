"""
Instagram 데이터 수집 라우터
인스타그램 프로필 및 게시물 데이터 수집 API
"""

from fastapi import APIRouter, HTTPException, status, Query, Request
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import (
    ProfileData,
    PostData,
    ProfileResponse,
    PostsResponse,
    ValidationResponse,
    ErrorResponse,
)
from app.services.instagram_service import (
    instagram_service,
    ProfileNotFoundError,
    PrivateAccountError,
    RateLimitError,
    InstagramServiceError,
)
from app.utils.logger import get_logger

logger = get_logger("instagram_router")
router = APIRouter()

# Rate Limiter 인스턴스
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/instagram/profile/{username}",
    response_model=ProfileResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Private account"},
        404: {"model": ErrorResponse, "description": "Profile not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="인스타그램 프로필 조회",
    description="특정 사용자명의 인스타그램 프로필 정보를 조회합니다.",
)
@limiter.limit("20/minute")  # 프로필 조회: 20회/분
async def get_instagram_profile(
    request: Request,  # slowapi를 위한 Request 객체
    username: str,
    use_cache: bool = Query(default=True, description="캐시 사용 여부"),
) -> ProfileResponse:
    """
    인스타그램 프로필 정보를 조회합니다.

    Args:
        username: 인스타그램 사용자명
        use_cache: 캐시 사용 여부 (기본값: True)

    Returns:
        ProfileResponse: 프로필 정보

    Raises:
        HTTPException: 프로필을 찾을 수 없거나 비공개 계정인 경우
    """
    try:
        profile_data = await instagram_service.fetch_profile(username, use_cache)
        return ProfileResponse(
            success=True,
            data=profile_data,
            cached=False,  # 캐시에서 가져온 경우는 서비스 낶에서 처리
        )

    except ProfileNotFoundError as e:
        logger.warning("profile_not_found", username=username)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Profile not found",
                "detail": str(e.message),
                "code": e.code,
            },
        )

    except PrivateAccountError as e:
        logger.warning("private_account_requested", username=username)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Private account",
                "detail": str(e.message),
                "code": e.code,
            },
        )

    except RateLimitError as e:
        logger.error("rate_limit_hit", username=username)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "detail": str(e.message),
                "code": e.code,
            },
        )

    except InstagramServiceError as e:
        logger.error("instagram_service_error", username=username, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Instagram service error",
                "detail": str(e.message),
                "code": e.code,
            },
        )

    except Exception as e:
        logger.error("unexpected_error", username=username, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": str(e),
                "code": "internal_error",
            },
        )


@router.get(
    "/instagram/posts/{username}",
    response_model=PostsResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Private account"},
        404: {"model": ErrorResponse, "description": "Profile not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="인스타그램 게시물 조회",
    description="특정 사용자의 최근 게시물 목록을 조회합니다.",
)
async def get_instagram_posts(
    username: str,
    limit: int = Query(default=20, ge=1, le=50, description="조회할 게시물 수 (1-50)"),
    use_cache: bool = Query(default=True, description="캐시 사용 여부"),
) -> PostsResponse:
    """
    인스타그램 게시물 목록을 조회합니다.

    Args:
        username: 인스타그램 사용자명
        limit: 조회할 게시물 수 (기본값: 20, 최대: 50)
        use_cache: 캐시 사용 여부 (기본값: True)

    Returns:
        PostsResponse: 게시물 목록

    Raises:
        HTTPException: 프로필을 찾을 수 없거나 비공개 계정인 경우
    """
    try:
        posts_data = await instagram_service.fetch_posts(username, limit, use_cache)
        return PostsResponse(
            success=True,
            username=username.lower(),
            posts=posts_data,
            total_count=len(posts_data),
            fetched_count=len(posts_data),
            cached=False,
        )

    except ProfileNotFoundError as e:
        logger.warning("profile_not_found_for_posts", username=username)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "Profile not found",
                "detail": str(e.message),
                "code": e.code,
            },
        )

    except PrivateAccountError as e:
        logger.warning("private_account_posts_requested", username=username)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Private account",
                "detail": str(e.message),
                "code": e.code,
            },
        )

    except RateLimitError as e:
        logger.error("rate_limit_hit_posts", username=username)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "detail": str(e.message),
                "code": e.code,
            },
        )

    except InstagramServiceError as e:
        logger.error("instagram_service_error_posts", username=username, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Instagram service error",
                "detail": str(e.message),
                "code": e.code,
            },
        )

    except Exception as e:
        logger.error("unexpected_error_posts", username=username, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal server error",
                "detail": str(e),
                "code": "internal_error",
            },
        )


@router.post(
    "/instagram/validate/{username}",
    response_model=ValidationResponse,
    responses={
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="사용자명 유효성 검사",
    description="인스타그램 사용자명이 유효한지 검사하고 계정 존재 여부를 확인합니다.",
)
async def validate_username(username: str) -> ValidationResponse:
    """
    인스타그램 사용자명의 유효성을 검사합니다.

    Args:
        username: 검사할 사용자명

    Returns:
        ValidationResponse: 검사 결과
    """
    try:
        result = await instagram_service.validate_username(username)
        return ValidationResponse(**result)

    except RateLimitError as e:
        logger.error("rate_limit_hit_validate", username=username)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "detail": str(e.message),
                "code": e.code,
            },
        )

    except Exception as e:
        logger.error("validate_error", username=username, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Validation error",
                "detail": str(e),
                "code": "validation_error",
            },
        )

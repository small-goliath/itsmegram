"""
Instagram 데이터 수집 라우터
인스타그램 프로필 및 게시물 데이터 수집 API
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional

from app.models.schemas import InstagramProfile, ErrorResponse
from app.config import get_settings

router = APIRouter()


@router.get(
    "/instagram/profile/{username}",
    response_model=InstagramProfile,
    responses={
        404: {"model": ErrorResponse, "description": "Profile not found"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="인스타그램 프로필 조회",
    description="특정 사용자명의 인스타그램 프로필 정보를 조회합니다.",
)
async def get_instagram_profile(
    username: str,
) -> InstagramProfile:
    """
    인스타그램 프로필 정보를 조회합니다.

    Args:
        username: 인스타그램 사용자명

    Returns:
        InstagramProfile: 프로필 정보

    Raises:
        HTTPException: 프로필을 찾을 수 없는 경우
    """
    # TODO: 실제 인스타그램 데이터 수집 구현
    # 현재는 mock 데이터 반환
    if username.lower() in ["notfound", "error", "private"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile '{username}' not found or is private",
        )

    # Mock 데이터 (실제 구현 시 외부 API 연동)
    return InstagramProfile(
        username=username.lower(),
        full_name=f"{username.title()} User",
        biography=f"This is a mock biography for {username}",
        followers_count=15000,
        following_count=500,
        posts_count=250,
        profile_pic_url=None,
        is_private=False,
        is_verified=False,
        external_url=None,
    )


@router.get(
    "/instagram/posts/{username}",
    summary="인스타그램 게시물 조회",
    description="특정 사용자의 최근 게시물 목록을 조회합니다.",
)
async def get_instagram_posts(
    username: str,
    limit: int = 12,
) -> dict:
    """
    인스타그램 게시물 목록을 조회합니다.

    Args:
        username: 인스타그램 사용자명
        limit: 조회할 게시물 수 (기본값: 12)

    Returns:
        dict: 게시물 목록
    """
    # TODO: 실제 인스타그램 데이터 수집 구현
    settings = get_settings()

    return {
        "username": username.lower(),
        "posts": [],
        "total_count": 0,
        "message": "Not implemented yet - Mock data",
    }


@router.post(
    "/instagram/validate/{username}",
    summary="사용자명 유효성 검사",
    description="인스타그램 사용자명이 유효한지 검사합니다.",
)
async def validate_username(username: str) -> dict:
    """
    인스타그램 사용자명의 유효성을 검사합니다.

    Args:
        username: 검사할 사용자명

    Returns:
        dict: 검사 결과
    """
    import re

    pattern = r'^[a-zA-Z0-9._]{1,30}$'
    is_valid = bool(re.match(pattern, username))

    return {
        "username": username,
        "is_valid": is_valid,
        "message": "Valid username" if is_valid else "Invalid username format",
    }

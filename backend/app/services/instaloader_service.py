"""
instaloader 기반 Instagram 데이터 수집 서비스
로그인 인증을 통해 게시물 데이터를 수집합니다.
"""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any

import instaloader
import structlog

from app.config import get_settings
from app.utils.exceptions import (
    InstagramServiceError,
    ProfileNotFoundError,
    PrivateAccountError,
    RateLimitError,
)

logger = structlog.get_logger()

_loader: Optional[instaloader.Instaloader] = None
_logged_in: bool = False


def _get_loader() -> instaloader.Instaloader:
    """instaloader 인스턴스 반환 (싱글톤)"""
    global _loader
    if _loader is None:
        _loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_comments=False,
            save_metadata=False,
            quiet=True,
            sleep=True,  # 요청 간 자동 딜레이
            request_timeout=30,
        )
    return _loader


def _ensure_login() -> bool:
    """
    Instagram 로그인 확인 및 수행.
    환경 변수에 INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD가 설정된 경우에만 동작.
    """
    global _logged_in
    if _logged_in:
        return True

    settings = get_settings()
    username = settings.instagram_username
    password = settings.instagram_password

    if not username or not password:
        logger.warning("instagram_credentials_not_configured")
        return False

    try:
        L = _get_loader()
        L.login(username, password)
        _logged_in = True
        logger.info("instagram_login_success", username=username)
        return True
    except instaloader.exceptions.BadCredentialsException:
        logger.error("instagram_login_bad_credentials", username=username)
        return False
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        logger.error("instagram_login_2fa_required", username=username)
        return False
    except Exception as e:
        logger.error("instagram_login_failed", username=username, error=str(e))
        return False


def _fetch_posts_sync(username: str, limit: int) -> List[Dict[str, Any]]:
    """동기 방식으로 게시물 수집 (thread executor에서 실행)"""
    L = _get_loader()

    try:
        profile = instaloader.Profile.from_username(L.context, username)
    except instaloader.exceptions.ProfileNotExistsException:
        raise ProfileNotFoundError(username)
    except instaloader.exceptions.ConnectionException as e:
        if "401" in str(e) or "Unauthorized" in str(e):
            raise RateLimitError(f"Instagram 접근 차단 (로그인 필요): {username}")
        raise InstagramServiceError(f"연결 오류: {str(e)}")

    if profile.is_private:
        raise PrivateAccountError(username)

    posts = []
    try:
        for post in profile.get_posts():
            try:
                caption = post.caption or ""
                hashtags = [tag.lower() for tag in (post.caption_hashtags or [])]
                mentions = [m.lower() for m in (post.caption_mentions or [])]

                is_video = post.is_video
                if post.typename == "GraphSidecar":
                    post_type = "carousel"
                elif is_video:
                    post_type = "video"
                else:
                    post_type = "image"

                posts.append({
                    "post_id": str(post.mediaid),
                    "shortcode": post.shortcode,
                    "caption": caption,
                    "likes": post.likes,
                    "comments": post.comments,
                    "media_url": post.url,
                    "timestamp": post.date_utc,
                    "post_type": post_type,
                    "hashtags": hashtags,
                    "mentions": mentions,
                })
            except Exception as e:
                logger.warning("post_parse_error", shortcode=getattr(post, "shortcode", "?"), error=str(e))
                continue

            if len(posts) >= limit:
                break

    except instaloader.exceptions.ConnectionException as e:
        error_str = str(e)
        if "Please wait" in error_str or "wait a few minutes" in error_str:
            raise RateLimitError(f"Instagram 일시적 차단 (잠시 후 재시도): {username}")
        if posts:
            # 일부만 수집됐어도 반환
            logger.warning("partial_posts_collected", count=len(posts), error=str(e))
        else:
            raise InstagramServiceError(f"게시물 수집 중 연결 오류: {str(e)}")

    return posts


async def fetch_posts_with_login(username: str, limit: int = 12) -> List[Dict[str, Any]]:
    """
    Instagram 로그인을 통해 게시물 수집.

    Returns:
        게시물 딕셔너리 리스트

    Raises:
        InstagramServiceError: 자격증명 미설정 또는 로그인 실패
        ProfileNotFoundError: 프로필 없음
        PrivateAccountError: 비공개 계정
        RateLimitError: Instagram 차단
    """
    logged_in = await asyncio.to_thread(_ensure_login)
    if not logged_in:
        settings = get_settings()
        if not settings.instagram_username:
            raise InstagramServiceError(
                "Instagram 계정 설정이 필요합니다. "
                ".env 파일에 INSTAGRAM_USERNAME과 INSTAGRAM_PASSWORD를 설정해주세요."
            )
        raise InstagramServiceError(
            "Instagram 로그인에 실패했습니다. "
            ".env 파일의 INSTAGRAM_USERNAME과 INSTAGRAM_PASSWORD를 확인해주세요."
        )

    logger.info("fetching_posts_with_login", username=username, limit=limit)
    posts = await asyncio.to_thread(_fetch_posts_sync, username, limit)
    logger.info("posts_fetched_with_login", username=username, count=len(posts))
    return posts


def is_configured() -> bool:
    """Instagram 자격증명 설정 여부 확인"""
    settings = get_settings()
    return bool(settings.instagram_username and settings.instagram_password)


def reset_login():
    """로그인 상태 초기화 (재로그인용)"""
    global _loader, _logged_in
    _loader = None
    _logged_in = False

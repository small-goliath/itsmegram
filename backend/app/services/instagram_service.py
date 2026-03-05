"""
itsmegram - Instagram 데이터 수집 서비스
Instaloader를 사용하여 인스타그램 프로필 및 게시물 데이터 수집
"""

import asyncio
import re
from datetime import datetime
from typing import List, Optional, Dict, Any

import instaloader
from instaloader import Instaloader, Profile, Post
from instaloader.exceptions import (
    ProfileNotExistsException,
    ConnectionException,
    LoginRequiredException,
    TooManyRequestsException,
)

from app.models.schemas import ProfileData, PostData, InstagramData
from app.services.cache_service import cache_service
import structlog

logger = structlog.get_logger()


class InstagramServiceError(Exception):
    """Instagram 서비스 기본 예외"""
    def __init__(self, message: str, code: str = "instagram_error"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ProfileNotFoundError(InstagramServiceError):
    """프로필을 찾을 수 없는 경우"""
    def __init__(self, username: str):
        super().__init__(
            message=f"Profile '{username}' not found",
            code="profile_not_found"
        )
        self.username = username


class PrivateAccountError(InstagramServiceError):
    """비공개 계정인 경우"""
    def __init__(self, username: str):
        super().__init__(
            message=f"Account '{username}' is private and cannot be analyzed",
            code="private_account"
        )
        self.username = username


class RateLimitError(InstagramServiceError):
    """API Rate Limit에 걸린 경우"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            code="rate_limit"
        )


class InstagramService:
    """
    Instagram 데이터 수집 서비스
    - Instaloader를 사용한 프로필/게시물 데이터 수집
    - 캐싱 지원
    - 비동기 처리
    """

    def __init__(self):
        self._loader: Optional[Instaloader] = None
        self._lock = asyncio.Lock()

    async def _get_loader(self) -> Instaloader:
        """
        Instaloader 인스턴스 가져오기 (스레드 안전)
        """
        if self._loader is None:
            async with self._lock:
                if self._loader is None:
                    self._loader = Instaloader(
                        download_pictures=False,
                        download_videos=False,
                        download_video_thumbnails=False,
                        download_geotags=False,
                        download_comments=False,
                        save_metadata=False,
                        compress_json=False,
                        post_metadata_txt_pattern="",
                    )
                    logger.info("instaloader_initialized")
        return self._loader

    def _extract_hashtags(self, text: str) -> List[str]:
        """
        텍스트에서 해시태그 추출
        """
        if not text:
            return []
        hashtags = re.findall(r'#(\w+)', text)
        return [tag.lower() for tag in hashtags]

    def _extract_mentions(self, text: str) -> List[str]:
        """
        텍스트에서 멘션 추출
        """
        if not text:
            return []
        mentions = re.findall(r'@(\w+)', text)
        return [mention.lower() for mention in mentions]

    def _get_post_type(self, post: Post) -> str:
        """
        게시물 타입 결정
        """
        if post.typename == "GraphSidecar":
            return "carousel"
        elif post.is_video:
            return "video"
        else:
            return "image"

    def _get_media_url(self, post: Post) -> str:
        """
        게시물 미디어 URL 가져오기
        """
        try:
            if post.is_video and post.video_url:
                return post.video_url
            elif post.url:
                return post.url
            return ""
        except Exception:
            return ""

    async def fetch_profile(self, username: str, use_cache: bool = True) -> ProfileData:
        """
        인스타그램 프로필 정보 수집

        Args:
            username: 인스타그램 사용자명
            use_cache: 캐시 사용 여부

        Returns:
            ProfileData: 프로필 데이터

        Raises:
            ProfileNotFoundError: 프로필을 찾을 수 없는 경우
            PrivateAccountError: 비공개 계정인 경우
            RateLimitError: Rate limit에 걸린 경우
            InstagramServiceError: 기타 에러
        """
        # 캐시 확인 (30분 TTL)
        if use_cache:
            cached_data = await cache_service.get_cached_profile(username)
            if cached_data:
                logger.info("profile_cache_hit", username=username)
                return ProfileData(**cached_data)

        try:
            loader = await self._get_loader()

            # 동기식 Instaloader를 비동기로 실행
            loop = asyncio.get_event_loop()
            profile = await loop.run_in_executor(
                None,
                lambda: Profile.from_username(loader.context, username)
            )

            # 비공개 계정 체크
            if profile.is_private:
                logger.warning("private_account_access_denied", username=username)
                raise PrivateAccountError(username)

            profile_data = ProfileData(
                username=profile.username,
                full_name=profile.full_name or "",
                biography=profile.biography or "",
                followers=profile.followers,
                following=profile.followees,
                posts_count=profile.mediacount,
                is_private=profile.is_private,
                profile_pic_url=profile.profile_pic_url or "",
                is_verified=profile.is_verified,
                external_url=profile.external_url,
            )

            # 캐시 저장 (30분 TTL)
            if use_cache:
                await cache_service.cache_profile(
                    username,
                    profile_data.model_dump(),
                    ttl=1800  # 30분
                )

            logger.info(
                "profile_fetched",
                username=username,
                followers=profile_data.followers,
                posts=profile_data.posts_count,
            )

            return profile_data

        except ProfileNotExistsException as e:
            logger.error("profile_not_found", username=username, error=str(e))
            raise ProfileNotFoundError(username)

        except (TooManyRequestsException, ConnectionException) as e:
            logger.error("rate_limit_or_connection_error", username=username, error=str(e))
            raise RateLimitError(f"Instagram API limit exceeded: {str(e)}")

        except PrivateAccountError:
            raise

        except Exception as e:
            logger.error("profile_fetch_error", username=username, error=str(e))
            raise InstagramServiceError(
                message=f"Failed to fetch profile: {str(e)}",
                code="profile_fetch_error"
            )

    async def fetch_posts(
        self,
        username: str,
        limit: int = 20,
        use_cache: bool = True,
    ) -> List[PostData]:
        """
        인스타그램 게시물 수집

        Args:
            username: 인스타그램 사용자명
            limit: 수집할 게시물 수 (최대 50)
            use_cache: 캐시 사용 여부

        Returns:
            List[PostData]: 게시물 데이터 목록

        Raises:
            ProfileNotFoundError: 프로필을 찾을 수 없는 경우
            PrivateAccountError: 비공개 계정인 경우
            RateLimitError: Rate limit에 걸린 경우
        """
        limit = min(limit, 50)  # 최대 50개로 제한

        # 캐시 확인 (30분 TTL)
        if use_cache:
            cached_data = await cache_service.get_cached_posts(username, limit)
            if cached_data:
                logger.info("posts_cache_hit", username=username, limit=limit)
                return [PostData(**post) for post in cached_data]

        try:
            loader = await self._get_loader()

            # 프로필 가져오기
            loop = asyncio.get_event_loop()
            profile = await loop.run_in_executor(
                None,
                lambda: Profile.from_username(loader.context, username)
            )

            # 비공개 계정 체크
            if profile.is_private:
                logger.warning("private_account_posts_denied", username=username)
                raise PrivateAccountError(username)

            # 게시물 수집
            posts_data: List[PostData] = []
            posts_iterator = profile.get_posts()

            for idx, post in enumerate(posts_iterator):
                if idx >= limit:
                    break

                try:
                    post_data = PostData(
                        post_id=str(post.mediaid),
                        caption=post.caption or "",
                        likes=post.likes,
                        comments=post.comments,
                        media_url=self._get_media_url(post),
                        hashtags=self._extract_hashtags(post.caption or ""),
                        mentions=self._extract_mentions(post.caption or ""),
                        timestamp=post.date_local,
                        post_type=self._get_post_type(post),
                        shortcode=post.shortcode,
                    )
                    posts_data.append(post_data)

                except Exception as e:
                    logger.warning(
                        "post_parse_error",
                        username=username,
                        post_id=post.mediaid if hasattr(post, 'mediaid') else 'unknown',
                        error=str(e),
                    )
                    continue

            # 캐시 저장 (30분 TTL)
            if use_cache and posts_data:
                await cache_service.cache_posts(
                    username,
                    limit,
                    [post.model_dump() for post in posts_data],
                    ttl=1800  # 30분
                )

            logger.info(
                "posts_fetched",
                username=username,
                requested=limit,
                fetched=len(posts_data),
            )

            return posts_data

        except ProfileNotExistsException as e:
            logger.error("profile_not_found_for_posts", username=username, error=str(e))
            raise ProfileNotFoundError(username)

        except (TooManyRequestsException, ConnectionException) as e:
            logger.error("rate_limit_or_connection_error_posts", username=username, error=str(e))
            raise RateLimitError(f"Instagram API limit exceeded: {str(e)}")

        except PrivateAccountError:
            raise

        except Exception as e:
            logger.error("posts_fetch_error", username=username, error=str(e))
            raise InstagramServiceError(
                message=f"Failed to fetch posts: {str(e)}",
                code="posts_fetch_error"
            )

    async def fetch_full_data(
        self,
        username: str,
        posts_limit: int = 20,
        use_cache: bool = True,
    ) -> InstagramData:
        """
        프로필과 게시물 데이터를 한번에 수집

        Args:
            username: 인스타그램 사용자명
            posts_limit: 수집할 게시물 수
            use_cache: 캐시 사용 여부

        Returns:
            InstagramData: 전체 인스타그램 데이터
        """
        # 프로필과 게시물을 병렬로 가져오기
        profile_task = self.fetch_profile(username, use_cache)
        posts_task = self.fetch_posts(username, posts_limit, use_cache)

        profile, posts = await asyncio.gather(profile_task, posts_task)

        return InstagramData(
            profile=profile,
            posts=posts,
            collected_at=datetime.utcnow(),
        )

    async def validate_username(self, username: str) -> Dict[str, Any]:
        """
        사용자명 유효성 검사 및 계정 존재 여부 확인

        Args:
            username: 검사할 사용자명

        Returns:
            Dict: 검사 결과
        """
        # 기본 형식 검사
        if not re.match(r'^[a-zA-Z0-9._]{1,30}$', username):
            return {
                "username": username,
                "is_valid": False,
                "exists": None,
                "is_private": None,
                "message": "Invalid username format. Use 1-30 characters of letters, numbers, dots, or underscores.",
            }

        try:
            loader = await self._get_loader()
            loop = asyncio.get_event_loop()
            profile = await loop.run_in_executor(
                None,
                lambda: Profile.from_username(loader.context, username)
            )

            return {
                "username": username,
                "is_valid": True,
                "exists": True,
                "is_private": profile.is_private,
                "message": "Account exists and is valid",
            }

        except ProfileNotExistsException:
            return {
                "username": username,
                "is_valid": True,
                "exists": False,
                "is_private": None,
                "message": "Username format is valid but account does not exist",
            }

        except (TooManyRequestsException, ConnectionException) as e:
            return {
                "username": username,
                "is_valid": True,
                "exists": None,
                "is_private": None,
                "message": f"Could not verify account due to rate limiting: {str(e)}",
            }

        except Exception as e:
            logger.error("validate_username_error", username=username, error=str(e))
            return {
                "username": username,
                "is_valid": True,
                "exists": None,
                "is_private": None,
                "message": f"Error validating username: {str(e)}",
            }

    async def clear_cache(self, username: Optional[str] = None) -> bool:
        """
        캐시 삭제

        Args:
            username: 특정 사용자의 캐시만 삭제 (None이면 전체 삭제 시도)

        Returns:
            bool: 성공 여부
        """
        try:
            if username:
                # 특정 사용자 캐시 삭제 (새로운 메서드 사용)
                await cache_service.invalidate_profile(username)
                await cache_service.invalidate_posts(username)
                logger.info("cache_cleared_for_user", username=username)
            return True
        except Exception as e:
            logger.error("cache_clear_error", username=username, error=str(e))
            return False


# 싱글톤 인스턴스
instagram_service = InstagramService()

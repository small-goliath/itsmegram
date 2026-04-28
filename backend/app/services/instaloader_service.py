"""
Instagram 데이터 수집 서비스 (instagrapi 모바일 API 기반)
계정 풀링 + 세션 지속 + 자동 쿨다운으로 대규모 동시 사용 지원

instagrapi는 Instagram 모바일 API (i.instagram.com/api/v1/)를 사용하므로
웹 graphql/query 차단을 우회할 수 있음.
"""

import asyncio
import json
import os
import time
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

import structlog

from app.config import get_settings
from app.utils.exceptions import (
    InstagramServiceError,
    ProfileNotFoundError,
    PrivateAccountError,
    RateLimitError,
)

logger = structlog.get_logger()

SESSION_DIR = os.path.join(os.path.dirname(__file__), "..", "..", ".sessions")

# 쿨다운 설정 (초)
RATE_LIMIT_COOLDOWN = 300       # rate limit 시 5분
LOGIN_FAIL_COOLDOWN = 3600      # 로그인 실패 시 1시간
MIN_REQUEST_INTERVAL = 3        # 같은 계정의 최소 요청 간격
ACQUIRE_TIMEOUT = 30            # 계정 대기 최대 시간


@dataclass
class InstaAccount:
    """Instagram 계정 상태 관리"""
    username: str
    password: str
    client: Any = field(default=None, repr=False)  # instagrapi.Client
    logged_in: bool = False
    cooldown_until: float = 0
    in_use: bool = False
    request_count: int = 0
    last_request_time: float = 0
    consecutive_errors: int = 0


class AccountPool:
    """
    Instagram 계정 풀 (instagrapi 모바일 API 기반).
    - 다중 계정 로드밸런싱
    - 세션 파일 지속 (서버 재시작 시 재사용)
    - 자동 쿨다운 및 계정 전환
    - 스레드 안전 동시성 제어
    """

    def __init__(self):
        self._accounts: List[InstaAccount] = []
        self._lock = threading.Lock()
        self._initialized = False
        os.makedirs(SESSION_DIR, exist_ok=True)

    def _init_accounts(self):
        if self._initialized:
            return
        settings = get_settings()

        # INSTAGRAM_ACCOUNTS 파싱: "user1:pass1,user2:pass2"
        accounts_str = getattr(settings, "instagram_accounts", "")
        if accounts_str:
            for pair in accounts_str.split(","):
                pair = pair.strip()
                if ":" in pair:
                    u, p = pair.split(":", 1)
                    u, p = u.strip(), p.strip()
                    if u and p:
                        self._accounts.append(InstaAccount(username=u, password=p))

        # 단일 계정 폴백 (중복 방지)
        if settings.instagram_username and settings.instagram_password:
            existing = {a.username for a in self._accounts}
            if settings.instagram_username not in existing:
                self._accounts.append(
                    InstaAccount(
                        username=settings.instagram_username,
                        password=settings.instagram_password,
                    )
                )

        logger.info("account_pool_initialized", count=len(self._accounts))
        self._initialized = True

    @property
    def account_count(self) -> int:
        self._init_accounts()
        return len(self._accounts)

    def is_configured(self) -> bool:
        self._init_accounts()
        return len(self._accounts) > 0

    def acquire(self) -> Optional[InstaAccount]:
        """사용 가능한 계정 할당 (스레드 안전)"""
        self._init_accounts()
        with self._lock:
            now = time.time()
            best = None
            for acc in self._accounts:
                if acc.in_use:
                    continue
                if acc.cooldown_until > now:
                    continue
                if best is None:
                    best = acc
                elif acc.logged_in and not best.logged_in:
                    best = acc
                elif acc.consecutive_errors < best.consecutive_errors:
                    best = acc
                elif acc.request_count < best.request_count:
                    best = acc

            if best:
                best.in_use = True
                return best
            return None

    def release(self, account: InstaAccount, cooldown_seconds: int = 0):
        """계정 반환"""
        with self._lock:
            account.in_use = False
            if cooldown_seconds > 0:
                account.cooldown_until = time.time() + cooldown_seconds
                logger.warning(
                    "account_cooldown",
                    account=account.username,
                    seconds=cooldown_seconds,
                )

    def invalidate_session(self, account: InstaAccount):
        """세션 무효화 (재로그인 강제)"""
        account.logged_in = False
        account.client = None
        session_path = self._session_path(account.username)
        try:
            if os.path.exists(session_path):
                os.remove(session_path)
                logger.info("session_invalidated", account=account.username)
        except OSError:
            pass

    def _session_path(self, username: str) -> str:
        return os.path.join(SESSION_DIR, f"{username}.json")

    def ensure_login(self, account: InstaAccount) -> bool:
        """로그인 보장. 저장된 세션이 있으면 로드, 없으면 새로 로그인."""
        from instagrapi import Client
        from instagrapi.exceptions import (
            BadPassword,
            ChallengeRequired,
            TwoFactorRequired,
            LoginRequired,
        )

        if account.logged_in and account.client:
            return True

        if account.client is None:
            account.client = Client()
            account.client.delay_range = [3, 8]  # 요청 간 3~8초 랜덤 딜레이 (rate limit 방지)  # 요청 간 2~5초 랜덤 딜레이

        session_path = self._session_path(account.username)

        # 1) 저장된 세션 로드 시도
        if os.path.exists(session_path):
            try:
                account.client.load_settings(Path(session_path))
                account.client.login(account.username, account.password)
                account.logged_in = True
                logger.info("session_restored", account=account.username)
                return True
            except LoginRequired:
                logger.warning("session_expired", account=account.username)
                try:
                    os.remove(session_path)
                except OSError:
                    pass
                # 새 클라이언트로 재시도
                account.client = Client()
                account.client.delay_range = [3, 8]  # 요청 간 3~8초 랜덤 딜레이 (rate limit 방지)
            except Exception as e:
                logger.warning(
                    "session_restore_failed",
                    account=account.username,
                    error=str(e),
                )
                try:
                    os.remove(session_path)
                except OSError:
                    pass
                account.client = Client()
                account.client.delay_range = [3, 8]  # 요청 간 3~8초 랜덤 딜레이 (rate limit 방지)

        # 2) 새 로그인
        try:
            account.client.login(account.username, account.password)
            account.logged_in = True
            # 세션 저장
            try:
                account.client.dump_settings(Path(session_path))
                logger.info("login_success_session_saved", account=account.username)
            except Exception as e:
                logger.warning("session_save_failed", account=account.username, error=str(e))
                logger.info("login_success", account=account.username)
            return True
        except BadPassword:
            logger.error("login_bad_credentials", account=account.username)
            return False
        except TwoFactorRequired:
            logger.error("login_2fa_required", account=account.username)
            return False
        except ChallengeRequired:
            logger.error("login_challenge_required", account=account.username)
            return False
        except Exception as e:
            error_str = str(e)
            if "please wait" in error_str.lower() or "few minutes" in error_str.lower():
                logger.warning("login_rate_limited", account=account.username)
            else:
                logger.error("login_failed", account=account.username, error=error_str)
            return False

    def save_session(self, account: InstaAccount):
        """현재 세션을 파일에 저장"""
        if account.logged_in and account.client:
            try:
                account.client.dump_settings(Path(self._session_path(account.username)))
            except Exception:
                pass

    def get_status(self) -> List[Dict[str, Any]]:
        """풀 상태 조회 (모니터링/디버깅)"""
        self._init_accounts()
        now = time.time()
        return [
            {
                "account": acc.username,
                "logged_in": acc.logged_in,
                "in_use": acc.in_use,
                "cooldown_remaining": max(0, int(acc.cooldown_until - now)),
                "request_count": acc.request_count,
                "consecutive_errors": acc.consecutive_errors,
            }
            for acc in self._accounts
        ]


# ── 싱글톤 풀 ────────────────────────────────────────────────
_pool = AccountPool()


# ── 동기 데이터 수집 (thread executor 에서 실행) ──────────────

def _fetch_posts_sync(
    account: InstaAccount, username: str, limit: int
) -> List[Dict[str, Any]]:
    """게시물 수집 (동기, instagrapi 모바일 API)"""
    from instagrapi.exceptions import (
        UserNotFound,
        PrivateAccount,
        ClientThrottledError,
        ClientError,
        LoginRequired,
    )

    cl = account.client

    try:
        user_id = cl.user_id_from_username(username)
    except UserNotFound:
        raise ProfileNotFoundError(username)
    except (ClientThrottledError, LoginRequired) as e:
        logger.warning("instagrapi_throttled", account=account.username, target=username,
                       exc_type=type(e).__name__, error=str(e))
        raise RateLimitError(f"Instagram 일시적 차단: {username}")
    except ClientError as e:
        error_str = str(e)
        logger.warning("instagrapi_client_error", account=account.username, target=username,
                       exc_type=type(e).__name__, error=error_str)
        if "Please wait" in error_str or "login_required" in error_str.lower():
            raise RateLimitError(f"Instagram 일시적 차단: {username}")
        raise InstagramServiceError(f"연결 오류: {error_str}")
    except Exception as e:
        error_str = str(e)
        logger.error("instagrapi_unexpected_error", account=account.username, target=username,
                     exc_type=type(e).__name__, error=error_str)
        raise InstagramServiceError(f"예상치 못한 오류: {error_str}")

    try:
        user_info = cl.user_info(user_id)
    except Exception:
        user_info = None

    if user_info and user_info.is_private:
        raise PrivateAccountError(username)

    posts = []
    try:
        medias = cl.user_medias(user_id, amount=limit)
        for media in medias:
            try:
                caption = media.caption_text or ""

                # 해시태그 추출
                import re
                hashtags = [t.lower() for t in re.findall(r"#(\w+)", caption)]
                mentions = [m.lower() for m in re.findall(r"@(\w+)", caption)]

                # 미디어 타입 판별
                media_type = str(media.media_type)
                if media.media_type == 8:  # carousel
                    post_type = "carousel"
                elif media.media_type == 2:  # video
                    post_type = "video"
                else:
                    post_type = "image"

                # 미디어 URL
                media_url = ""
                if media.thumbnail_url:
                    media_url = str(media.thumbnail_url)
                elif media.resources and len(media.resources) > 0:
                    media_url = str(media.resources[0].thumbnail_url or "")

                posts.append({
                    "post_id": str(media.pk),
                    "shortcode": media.code,
                    "caption": caption,
                    "likes": media.like_count or 0,
                    "comments": media.comment_count or 0,
                    "media_url": media_url,
                    "timestamp": media.taken_at,
                    "post_type": post_type,
                    "hashtags": hashtags,
                    "mentions": mentions,
                })
            except Exception as e:
                logger.warning(
                    "post_parse_error",
                    shortcode=getattr(media, "code", "?"),
                    error=str(e),
                )
                continue

    except (ClientThrottledError, LoginRequired):
        if posts:
            logger.warning("partial_posts_collected", count=len(posts))
        else:
            raise RateLimitError(f"Instagram 일시적 차단: {username}")
    except ClientError as e:
        error_str = str(e)
        if "Please wait" in error_str or "login_required" in error_str.lower():
            if posts:
                logger.warning("partial_posts_collected", count=len(posts))
            else:
                raise RateLimitError(f"Instagram 일시적 차단: {username}")
        elif posts:
            logger.warning("partial_posts_collected", count=len(posts), error=error_str)
        else:
            raise InstagramServiceError(f"게시물 수집 중 오류: {error_str}")

    return posts


def _fetch_profile_sync(
    account: InstaAccount, username: str
) -> Dict[str, Any]:
    """프로필 정보 수집 (동기, instagrapi)"""
    from instagrapi.exceptions import (
        UserNotFound,
        ClientThrottledError,
        ClientError,
        LoginRequired,
    )

    cl = account.client

    try:
        user_id = cl.user_id_from_username(username)
        user_info = cl.user_info(user_id)
    except UserNotFound:
        raise ProfileNotFoundError(username)
    except (ClientThrottledError, LoginRequired):
        raise RateLimitError(f"Instagram 일시적 차단: {username}")
    except ClientError as e:
        error_str = str(e)
        if "Please wait" in error_str:
            raise RateLimitError(f"Instagram 일시적 차단: {username}")
        raise InstagramServiceError(f"프로필 조회 실패: {error_str}")

    profile_pic_url = str(user_info.profile_pic_url or "")

    # 인증된 세션으로 프로필 이미지 base64 변환 (이미지 저장 시 CDN 접근 우회용)
    profile_pic_base64 = ""
    if profile_pic_url:
        try:
            import base64 as _b64
            resp = cl.private.get(profile_pic_url)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
            encoded = _b64.b64encode(resp.content).decode("utf-8")
            profile_pic_base64 = f"data:{content_type};base64,{encoded}"
        except Exception as e:
            logger.warning("profile_pic_base64_failed", url=profile_pic_url, error=str(e))

    return {
        "username": user_info.username,
        "full_name": user_info.full_name or "",
        "biography": user_info.biography or "",
        "followers": user_info.follower_count or 0,
        "following": user_info.following_count or 0,
        "posts_count": user_info.media_count or 0,
        "is_private": user_info.is_private,
        "is_verified": user_info.is_verified,
        "profile_pic_url": profile_pic_url,          # 원본 URL (웹 표시용)
        "profile_pic_base64": profile_pic_base64,    # base64 (이미지 저장용)
        "external_url": str(user_info.external_url or ""),
    }


# ── 비동기 공개 API ──────────────────────────────────────────

async def _acquire_with_wait(timeout: float = ACQUIRE_TIMEOUT) -> Optional[InstaAccount]:
    """계정을 대기하며 할당받기"""
    start = time.time()
    while time.time() - start < timeout:
        account = _pool.acquire()
        if account:
            return account
        await asyncio.sleep(1)
    return None


async def fetch_posts_with_login(
    username: str, limit: int = 12
) -> List[Dict[str, Any]]:
    """
    계정 풀에서 사용 가능한 계정을 할당받아 게시물 수집.
    rate limit 시 다른 계정으로 자동 재시도.
    """
    if not _pool.is_configured():
        raise InstagramServiceError(
            "Instagram 계정 설정이 필요합니다. "
            ".env 파일에 INSTAGRAM_USERNAME/INSTAGRAM_PASSWORD 또는 "
            "INSTAGRAM_ACCOUNTS를 설정해주세요."
        )

    max_attempts = min(_pool.account_count, 5)
    last_error: Optional[Exception] = None
    tried_accounts: set = set()

    for attempt in range(max_attempts):
        account = await _acquire_with_wait()
        if not account:
            raise RateLimitError(
                "모든 Instagram 계정이 사용 중이거나 일시 차단 상태입니다. "
                "잠시 후 다시 시도해주세요."
            )

        # 이미 시도한 계정이면 스킵
        if account.username in tried_accounts:
            _pool.release(account)
            await asyncio.sleep(2)
            continue

        try:
            # 로그인
            logged_in = await asyncio.to_thread(_pool.ensure_login, account)
            if not logged_in:
                tried_accounts.add(account.username)
                _pool.release(account, cooldown_seconds=LOGIN_FAIL_COOLDOWN)
                last_error = InstagramServiceError("Instagram 로그인 실패")
                continue

            # 최소 요청 간격 적용
            now = time.time()
            wait_time = account.last_request_time + MIN_REQUEST_INTERVAL - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)

            # 게시물 수집
            logger.info(
                "fetching_posts",
                account=account.username,
                target=username,
                attempt=attempt + 1,
            )
            posts = await asyncio.to_thread(
                _fetch_posts_sync, account, username, limit
            )

            # 성공
            account.request_count += 1
            account.last_request_time = time.time()
            account.consecutive_errors = 0
            _pool.save_session(account)
            _pool.release(account)

            logger.info(
                "posts_fetched",
                account=account.username,
                target=username,
                count=len(posts),
            )
            return posts

        except RateLimitError as e:
            tried_accounts.add(account.username)
            account.consecutive_errors += 1

            # 연속 2회 이상 실패 → 세션 무효화
            if account.consecutive_errors >= 2:
                _pool.invalidate_session(account)

            _pool.release(account, cooldown_seconds=RATE_LIMIT_COOLDOWN)
            last_error = e
            logger.warning(
                "account_rate_limited_retrying",
                account=account.username,
                target=username,
                attempt=attempt + 1,
                remaining_accounts=_pool.account_count - len(tried_accounts),
            )
            continue

        except (ProfileNotFoundError, PrivateAccountError):
            _pool.release(account)
            raise

        except Exception as e:
            account.consecutive_errors += 1
            _pool.release(account)
            raise

    # 모든 계정 소진
    if last_error:
        raise last_error
    raise RateLimitError(
        "모든 Instagram 계정이 일시 차단 상태입니다. 잠시 후 다시 시도해주세요."
    )


async def fetch_profile_with_login(username: str) -> Dict[str, Any]:
    """계정 풀에서 계정을 할당받아 프로필 수집"""
    if not _pool.is_configured():
        raise InstagramServiceError("Instagram 계정 미설정")

    account = await _acquire_with_wait()
    if not account:
        raise RateLimitError("모든 Instagram 계정이 사용 중입니다.")

    try:
        logged_in = await asyncio.to_thread(_pool.ensure_login, account)
        if not logged_in:
            _pool.release(account, cooldown_seconds=LOGIN_FAIL_COOLDOWN)
            raise InstagramServiceError("Instagram 로그인 실패")

        profile = await asyncio.to_thread(
            _fetch_profile_sync, account, username
        )
        account.request_count += 1
        account.last_request_time = time.time()
        _pool.release(account)
        return profile

    except (RateLimitError, ProfileNotFoundError, PrivateAccountError):
        _pool.release(account)
        raise
    except Exception:
        _pool.release(account)
        raise


# ── 유틸리티 ──────────────────────────────────────────────────

def is_configured() -> bool:
    return _pool.is_configured()


def get_pool_status() -> List[Dict[str, Any]]:
    return _pool.get_status()


def reset_pool():
    """전체 풀 초기화 (재시작용)"""
    global _pool
    _pool = AccountPool()


# 하위 호환
reset_login = reset_pool

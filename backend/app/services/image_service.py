"""
itsmegram - 리포트 이미지 생성 서비스
Playwright를 사용하여 Instagram 스토리 형식의 리포트 이미지 생성
"""

import base64
import io
import os
from typing import Optional, Dict, Any
from datetime import timedelta

import httpx
from playwright.async_api import async_playwright, Browser, Page
from jinja2 import Environment, FileSystemLoader, select_autoescape
import structlog

from app.models.report import Report
from app.services.cache_service import cache_service

logger = structlog.get_logger()


class ImageServiceError(Exception):
    """이미지 서비스 기본 예외"""
    def __init__(self, message: str, code: str = "image_service_error"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ImageGenerationError(ImageServiceError):
    """이미지 생성 실패 예외"""
    def __init__(self, message: str):
        super().__init__(message, "image_generation_error")


class TemplateRenderError(ImageServiceError):
    """템플릿 렌더링 실패 예외"""
    def __init__(self, message: str):
        super().__init__(message, "template_render_error")


class ReportImageService:
    """
    리포트 이미지 생성 서비스
    - HTML 템플릿 렌더링
    - Playwright를 사용한 스크린샷 생성
    - Redis 캐싱 지원 (1시간 TTL)
    """

    # Instagram 스토리 형식
    VIEWPORT_WIDTH = 1080
    VIEWPORT_HEIGHT = 1920

    # 이미지 캐시 TTL (1시간)
    IMAGE_CACHE_TTL = 3600

    def __init__(self):
        self._template_dir = self._get_template_dir()
        self._jinja_env = Environment(
            loader=FileSystemLoader(self._template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
        logger.info(
            "image_service_initialized",
            template_dir=self._template_dir,
            viewport=(self.VIEWPORT_WIDTH, self.VIEWPORT_HEIGHT)
        )

    def _get_template_dir(self) -> str:
        """템플릿 디렉토리 경로 반환"""
        # 현재 파일 기준으로 templates 디렉토리 찾기
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(os.path.dirname(current_dir))
        template_dir = os.path.join(backend_dir, "templates")

        if not os.path.exists(template_dir):
            # 대체 경로 시도
            template_dir = os.path.join(backend_dir, "app", "templates")

        return template_dir

    def _get_cache_key(self, report_id: str) -> str:
        """이미지 캐시 키 생성"""
        return f"report:image:{report_id}"

    async def _fetch_image_as_base64(self, url: str) -> Optional[str]:
        """
        외부 이미지 URL을 base64 data URI로 변환

        Args:
            url: 이미지 URL

        Returns:
            base64 data URI 문자열 또는 None
        """
        if not url:
            return None
        # 이미 base64 data URI인 경우 그대로 반환
        if url.startswith("data:"):
            return url
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "image/jpeg").split(";")[0]
                encoded = base64.b64encode(resp.content).decode("utf-8")
                return f"data:{content_type};base64,{encoded}"
        except Exception as e:
            logger.warning("profile_image_fetch_failed", url=url, error=str(e))
            return None

    def _render_template(self, report: Report, profile_image_data_uri: Optional[str] = None) -> str:
        """
        리포트 데이터를 HTML 템플릿에 렌더링

        Args:
            report: 리포트 모델
            profile_image_data_uri: base64로 인코딩된 프로필 이미지 (없으면 원본 URL 사용)

        Returns:
            렌더링된 HTML 문자열
        """
        try:
            template = self._jinja_env.get_template("report_story.html")

            # 템플릿에 전달할 컨텍스트 준비
            context = {
                # 기본 정보
                "username": report.username,
                "profile_image_url": profile_image_data_uri or report.profile_image_url,

                # 핵심 지표
                "engagement_rate": report.basic_metrics.get("engagement_rate", 0),
                "avg_likes": report.basic_metrics.get("avg_likes", 0),
                "avg_comments": report.basic_metrics.get("avg_comments", 0),
                "posts_count": report.collected_posts_count,

                # 콘텐츠 성향
                "categories": report.content_tendency.get("categories", []),
                "visual_style": report.content_tendency.get("visual_style", ""),
                "text_style": report.content_tendency.get("text_style", ""),
                "hashtag_pattern": report.content_tendency.get("hashtag_pattern", []),
                "posting_frequency": report.content_tendency.get("posting_frequency", ""),

                # 라이프스타일
                "interests": report.lifestyle.get("interests", []),
                "activity_pattern": report.lifestyle.get("activity_pattern", ""),
                "consumption": report.lifestyle.get("consumption", []),

                # 성격 분석
                "expression_strength": report.personality.get("expression_strength", 0),
                "extroversion": report.personality.get("extroversion", ""),
                "communication": report.personality.get("communication", ""),

                # 종합 요약
                "summary": report.summary,
            }

            html_content = template.render(**context)
            logger.debug(
                "template_rendered",
                report_id=report.id,
                username=report.username
            )
            return html_content

        except Exception as e:
            logger.error(
                "template_render_error",
                report_id=report.id,
                error=str(e)
            )
            raise TemplateRenderError(f"Failed to render template: {str(e)}")

    async def _generate_screenshot(self, html_content: str) -> bytes:
        """
        Playwright를 사용하여 HTML을 이미지로 변환

        Args:
            html_content: 렌더링된 HTML 문자열

        Returns:
            PNG 이미지 바이트
        """
        browser: Optional[Browser] = None

        try:
            async with async_playwright() as p:
                # Chromium 브라우저 실행
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--disable-gpu',
                        '--font-render-hinting=none',
                    ]
                )

                # 새 페이지 생성
                page = await browser.new_page()

                # 뷰포트 설정 (Instagram 스토리 형식)
                await page.set_viewport_size({
                    "width": self.VIEWPORT_WIDTH,
                    "height": self.VIEWPORT_HEIGHT
                })

                # HTML 콘텐츠 설정
                await page.set_content(html_content, wait_until="networkidle")

                # 폰트 로딩 대기
                await page.wait_for_timeout(1000)

                # 페이지 높이 계산
                page_height = await page.evaluate("document.body.scrollHeight")

                # 스크린샷 촬영
                screenshot = await page.screenshot(
                    full_page=True,
                    type="png",
                )

                logger.debug(
                    "screenshot_generated",
                    width=self.VIEWPORT_WIDTH,
                    height=max(page_height, self.VIEWPORT_HEIGHT),
                    size_bytes=len(screenshot)
                )

                return screenshot

        except Exception as e:
            logger.error("screenshot_generation_error", error=str(e))
            raise ImageGenerationError(f"Failed to generate screenshot: {str(e)}")

        finally:
            if browser:
                await browser.close()

    async def _get_cached_image(self, report_id: str) -> Optional[bytes]:
        """
        캐시에서 이미지 조회

        Args:
            report_id: 리포트 ID

        Returns:
            캐시된 이미지 바이트 또는 None
        """
        try:
            cache_key = self._get_cache_key(report_id)
            cached_data = await cache_service.get(cache_key)

            if cached_data:
                # Base64 디코딩
                image_bytes = base64.b64decode(cached_data)
                logger.debug(
                    "image_cache_hit",
                    report_id=report_id,
                    size_bytes=len(image_bytes)
                )
                return image_bytes

            return None

        except Exception as e:
            logger.warning("image_cache_get_error", report_id=report_id, error=str(e))
            return None

    async def _cache_image(self, report_id: str, image_bytes: bytes) -> bool:
        """
        이미지를 캐시에 저장

        Args:
            report_id: 리포트 ID
            image_bytes: 이미지 바이트

        Returns:
            캐싱 성공 여부
        """
        try:
            # Base64 인코딩
            encoded = base64.b64encode(image_bytes).decode('utf-8')

            cache_key = self._get_cache_key(report_id)
            success = await cache_service.set(
                cache_key,
                encoded,
                ttl=self.IMAGE_CACHE_TTL
            )

            if success:
                logger.debug(
                    "image_cached",
                    report_id=report_id,
                    ttl_seconds=self.IMAGE_CACHE_TTL
                )

            return success

        except Exception as e:
            logger.warning("image_cache_set_error", report_id=report_id, error=str(e))
            return False

    async def generate_report_image(
        self,
        report: Report,
        use_cache: bool = True
    ) -> bytes:
        """
        리포트 이미지 생성

        Args:
            report: 리포트 모델
            use_cache: 캐시 사용 여부

        Returns:
            PNG 이미지 바이트

        Raises:
            ImageGenerationError: 이미지 생성 실패 시
            TemplateRenderError: 템플릿 렌더링 실패 시
        """
        report_id = report.id

        # 캐시 확인
        if use_cache:
            cached_image = await self._get_cached_image(report_id)
            if cached_image:
                logger.info(
                    "report_image_served_from_cache",
                    report_id=report_id,
                    username=report.username
                )
                return cached_image

        logger.info(
            "generating_report_image",
            report_id=report_id,
            username=report.username
        )

        # 프로필 이미지 base64 확보 (Playwright 렌더링 시 CORS 우회)
        # 수집 시점에 저장된 base64가 있으면 우선 사용, 없으면 URL 직접 fetch 시도
        profile_image_data_uri = (
            report.profile_image_base64
            or await self._fetch_image_as_base64(report.profile_image_url)
        )

        # HTML 템플릿 렌더링
        html_content = self._render_template(report, profile_image_data_uri)

        # 스크린샷 생성
        image_bytes = await self._generate_screenshot(html_content)

        # 캐시에 저장
        if use_cache:
            await self._cache_image(report_id, image_bytes)

        logger.info(
            "report_image_generated",
            report_id=report_id,
            username=report.username,
            size_bytes=len(image_bytes)
        )

        return image_bytes

    async def invalidate_cache(self, report_id: str) -> bool:
        """
        리포트 이미지 캐시 무효화

        Args:
            report_id: 리포트 ID

        Returns:
            무효화 성공 여부
        """
        try:
            cache_key = self._get_cache_key(report_id)
            success = await cache_service.delete(cache_key)

            if success:
                logger.info("image_cache_invalidated", report_id=report_id)

            return success

        except Exception as e:
            logger.error("image_cache_invalidate_error", report_id=report_id, error=str(e))
            return False

    async def get_cache_info(self, report_id: str) -> Dict[str, Any]:
        """
        이미지 캐시 정보 조회

        Args:
            report_id: 리포트 ID

        Returns:
            캐시 정보 딕셔너리
        """
        cache_key = self._get_cache_key(report_id)
        exists = await cache_service.exists(cache_key)

        return {
            "report_id": report_id,
            "cached": exists,
            "cache_key": cache_key,
            "ttl_seconds": self.IMAGE_CACHE_TTL if exists else 0,
        }


# 싱글톤 인스턴스
report_image_service = ReportImageService()

"""
itsmegram - 리포트 생성 서비스
인스타그램 데이터 수집 및 AI 분석을 통해 리포트 생성
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

import structlog

from app.models.report import Report
from app.models.schemas import InstagramData
from app.services.storage_service import ReportStorage
from app.services.ai_service import AIService, AIServiceError
from app.services.instagram_service import InstagramService
from app.services.analytics_service import analytics_service
from app.utils.exceptions import (
    InstagramServiceError,
    ProfileNotFoundError,
    PrivateAccountError,
    RateLimitError,
    ReportServiceError,
    ReportNotFoundError,
    ReportExpiredError,
    ReportCreationError,
    MoonshotAPIError,
    AnalysisTimeoutError,
    AnalysisParsingError,
)
from app.config import get_settings

settings = get_settings()

logger = structlog.get_logger()


def _get_user_friendly_error_message(e: Exception) -> str:
    """예외를 사용자 친화적인 메시지로 변환"""
    if isinstance(e, ProfileNotFoundError):
        username = getattr(e, "username", "")
        return f"@{username} 계정을 찾을 수 없습니다. 아이디를 다시 확인해주세요."
    if isinstance(e, PrivateAccountError):
        return "비공개 계정은 분석할 수 없습니다. 계정을 공개로 전환한 후 다시 시도해주세요."
    if isinstance(e, RateLimitError):
        msg = str(e)
        if "Access denied" in msg or "접근 차단" in msg or "로그인" in msg:
            return (
                "Instagram 접근이 차단되어 게시물 데이터를 수집할 수 없습니다. "
            )
        return "인스타그램에서 일시적으로 요청을 제한하고 있습니다. 잠시 후 다시 시도해주세요."
    if isinstance(e, AnalysisTimeoutError):
        return "분석 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
    if isinstance(e, AnalysisParsingError):
        return "AI 분석 결과를 처리하는 중 오류가 발생했습니다. 다시 시도해주세요."
    if isinstance(e, MoonshotAPIError):
        msg = str(e).lower()
        if "401" in msg or "authentication" in msg or "invalid" in msg:
            return "AI 분석 서비스에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
        if "429" in msg or "rate" in msg:
            return "AI 분석 서비스 요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
        return "AI 분석 서비스에 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    if isinstance(e, AIServiceError):
        return "AI 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    if isinstance(e, InstagramServiceError):
        msg = str(e)
        if "INSTAGRAM_USERNAME" in msg or "로그인" in msg or "접근 제한" in msg:
            return (
                "게시물 데이터를 수집할 수 없어 분석을 진행할 수 없습니다. "
                "Instagram의 접근 제한으로 게시물을 가져오지 못했습니다. "
                "서버 .env 파일에 INSTAGRAM_USERNAME과 INSTAGRAM_PASSWORD를 설정해주세요."
            )
        return "인스타그램 데이터를 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    return "분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."


class ReportService:
    """
    리포트 생성 및 관리 서비스
    - 인스타그램 데이터 수집
    - AI 분석 수행
    - 리포트 저장 및 조회
    """

    def __init__(
        self,
        storage: Optional[ReportStorage] = None,
        ai_service: Optional[AIService] = None,
        instagram_service: Optional[InstagramService] = None
    ):
        self.storage = storage or ReportStorage()
        self.ai_service = ai_service or AIService()
        self.instagram_service = instagram_service or InstagramService()
        logger.info("report_service_initialized")

    async def create_report(self, username: str) -> str:
        """
        새로운 리포트 생성

        Args:
            username: 분석할 인스타그램 사용자명

        Returns:
            str: 생성된 리포트 ID

        Raises:
            ReportCreationError: 리포트 생성 실패 시
        """
        logger.info("starting_report_creation", username=username)

        # 1. 리포트 생성 (processing 상태)
        report = Report(
            username=username,
            status="processing"
        )

        try:
            await self.storage.save_report(report)
            logger.info("report_created", report_id=report.id, username=username)

            # 2. 인스타그램 데이터 수집
            try:
                instagram_data = await self.instagram_service.fetch_full_data(
                    username=username,
                    posts_limit=20,
                    use_cache=True
                )
                logger.info(
                    "instagram_data_collected",
                    report_id=report.id,
                    username=username,
                    posts_count=len(instagram_data.posts)
                )
            except ProfileNotFoundError as e:
                error_msg = f"@{username} 계정을 찾을 수 없습니다. 아이디를 다시 확인해주세요."
                await self._mark_report_failed(report.id, error_msg)
                await analytics_service.track_analysis_failed(
                    report_id=report.id,
                    username=username,
                    error_message=error_msg,
                )
                raise ReportCreationError(error_msg, username=username)

            except PrivateAccountError as e:
                error_msg = "비공개 계정은 분석할 수 없습니다. 계정을 공개로 전환한 후 다시 시도해주세요."
                await self._mark_report_failed(report.id, error_msg)
                await analytics_service.track_analysis_failed(
                    report_id=report.id,
                    username=username,
                    error_message=error_msg,
                )
                raise ReportCreationError(error_msg, username=username)

            except RateLimitError as e:
                _msg = str(e)
                if "Access denied" in _msg or "접근 차단" in _msg or "로그인" in _msg:
                    error_msg = (
                        "Instagram 접근이 차단되어 게시물 데이터를 수집할 수 없습니다. "
                    )
                else:
                    error_msg = "인스타그램에서 일시적으로 요청을 제한하고 있습니다. 잠시 후 다시 시도해주세요."
                await self._mark_report_failed(report.id, error_msg)
                await analytics_service.track_analysis_failed(
                    report_id=report.id,
                    username=username,
                    error_message=error_msg,
                )
                raise ReportCreationError(error_msg, username=username)

            except InstagramServiceError as e:
                error_msg = "인스타그램 데이터를 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
                await self._mark_report_failed(report.id, error_msg)
                await analytics_service.track_analysis_failed(
                    report_id=report.id,
                    username=username,
                    error_message=error_msg,
                )
                raise ReportCreationError(error_msg, username=username)

            # 3. AI 분석 수행
            try:
                analysis_result = await self.ai_service.analyze_profile(instagram_data)
                logger.info(
                    "ai_analysis_completed",
                    report_id=report.id,
                    username=username,
                    has_summary="summary" in analysis_result
                )
            except AnalysisTimeoutError:
                error_msg = "분석 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
                await self._mark_report_failed(report.id, error_msg)
                await analytics_service.track_analysis_failed(
                    report_id=report.id,
                    username=username,
                    error_message=error_msg,
                )
                raise ReportCreationError(error_msg, username=username)

            except AnalysisParsingError:
                error_msg = "AI 분석 결과를 처리하는 중 오류가 발생했습니다. 다시 시도해주세요."
                await self._mark_report_failed(report.id, error_msg)
                await analytics_service.track_analysis_failed(
                    report_id=report.id,
                    username=username,
                    error_message=error_msg,
                )
                raise ReportCreationError(error_msg, username=username)

            except MoonshotAPIError as e:
                raw = str(e).lower()
                if "401" in raw or "authentication" in raw or "invalid" in raw:
                    error_msg = "AI 분석 서비스에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요."
                elif "429" in raw or "rate" in raw:
                    error_msg = "AI 분석 서비스 요청이 너무 많습니다. 잠시 후 다시 시도해주세요."
                else:
                    error_msg = "AI 분석 서비스에 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
                await self._mark_report_failed(report.id, error_msg)
                await analytics_service.track_analysis_failed(
                    report_id=report.id,
                    username=username,
                    error_message=error_msg,
                )
                raise ReportCreationError(error_msg, username=username)

            except AIServiceError:
                error_msg = "AI 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
                await self._mark_report_failed(report.id, error_msg)
                await analytics_service.track_analysis_failed(
                    report_id=report.id,
                    username=username,
                    error_message=error_msg,
                )
                raise ReportCreationError(error_msg, username=username)

            except Exception:
                error_msg = "분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
                await self._mark_report_failed(report.id, error_msg)
                await analytics_service.track_analysis_failed(
                    report_id=report.id,
                    username=username,
                    error_message=error_msg,
                )
                raise ReportCreationError(error_msg, username=username)

            # 4. 리포트 데이터 업데이트
            try:
                report.basic_metrics = analysis_result.get("basic_metrics", {})
                report.content_tendency = analysis_result.get("content_tendency", {})
                report.lifestyle = analysis_result.get("lifestyle", {})
                report.personality = analysis_result.get("personality", {})
                report.network = analysis_result.get("network", {})
                report.growth_potential = analysis_result.get("growth_potential", {})
                report.summary = analysis_result.get("summary", "")
                report.profile_image_url = instagram_data.profile.profile_pic_url
                report.profile_image_base64 = instagram_data.profile.profile_pic_base64
                report.collected_posts_count = len(instagram_data.posts)
                report.status = "completed"

                await self.storage.save_report(report)

                logger.info(
                    "report_completed",
                    report_id=report.id,
                    username=username,
                    status="completed"
                )

                await analytics_service.track_analysis_complete(
                    report_id=report.id,
                    username=username,
                    metadata={
                        "posts_count": len(instagram_data.posts),
                        "followers": instagram_data.profile.followers,
                    },
                )

                return report.id

            except Exception:
                error_msg = "리포트 저장 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
                await self._mark_report_failed(report.id, error_msg)
                await analytics_service.track_analysis_failed(
                    report_id=report.id,
                    username=username,
                    error_message=error_msg,
                )
                raise ReportCreationError(error_msg, username=username)

        except ReportCreationError:
            raise
        except Exception as e:
            error_msg = "분석 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
            logger.error("unexpected_report_creation_error", username=username, error=str(e))
            try:
                await self._mark_report_failed(report.id, error_msg)
                await analytics_service.track_analysis_failed(
                    report_id=report.id,
                    username=username,
                    error_message=error_msg,
                )
            except:
                pass
            raise ReportCreationError(error_msg, username=username)

    async def _mark_report_failed(self, report_id: str, error_message: str):
        """리포트를 실패 상태로 표시"""
        try:
            await self.storage.update_report_status(
                report_id=report_id,
                status="failed",
                error_message=error_message
            )
            logger.info("report_marked_as_failed", report_id=report_id, error=error_message)
        except Exception as e:
            logger.error("failed_to_mark_report_failed", report_id=report_id, error=str(e))

    async def get_report(self, report_id: str) -> Optional[Report]:
        """
        리포트 조회

        Args:
            report_id: 리포트 ID

        Returns:
            Report: 리포트 객체 또는 None

        Raises:
            ReportNotFoundError: 리포트를 찾을 수 없는 경우
            ReportExpiredError: 리포트가 만료된 경우
        """
        try:
            report = await self.storage.get_report(report_id)

            if not report:
                logger.warning("report_not_found", report_id=report_id)
                raise ReportNotFoundError(report_id)

            if report.is_expired():
                logger.warning("report_expired", report_id=report_id)
                raise ReportExpiredError(report_id)

            logger.debug("report_found", report_id=report_id, status=report.status)
            return report

        except ReportNotFoundError:
            raise ReportNotFoundError(report_id)
        except ReportExpiredError:
            raise ReportExpiredError(report_id)
        except Exception as e:
            logger.error("report_get_error", report_id=report_id, error=str(e))
            raise ReportServiceError(f"Failed to get report: {str(e)}")

    async def delete_report(self, report_id: str) -> bool:
        """
        리포트 삭제

        Args:
            report_id: 삭제할 리포트 ID

        Returns:
            bool: 삭제 성공 여부
        """
        try:
            result = await self.storage.delete_report(report_id)
            if result:
                logger.info("report_deleted", report_id=report_id)
            else:
                logger.warning("report_not_found_for_deletion", report_id=report_id)
            return result

        except Exception as e:
            logger.error("report_delete_error", report_id=report_id, error=str(e))
            raise ReportServiceError(f"Failed to delete report: {str(e)}")

    async def get_report_status(self, report_id: str) -> Dict[str, Any]:
        """
        리포트 상태 조회

        Args:
            report_id: 리포트 ID

        Returns:
            Dict: 리포트 상태 정보
        """
        try:
            report = await self.get_report(report_id)

            return {
                "report_id": report.id,
                "username": report.username,
                "status": report.status,
                "created_at": report.created_at.isoformat(),
                "expires_at": report.expires_at.isoformat(),
                "is_expired": report.is_expired(),
                "error_message": report.error_message,
            }

        except ReportNotFoundError:
            return {
                "report_id": report_id,
                "status": "not_found",
                "error_message": f"Report '{report_id}' not found",
            }

        except ReportExpiredError:
            return {
                "report_id": report_id,
                "status": "expired",
                "error_message": f"Report '{report_id}' has expired",
            }

    async def wait_for_report(
        self,
        report_id: str,
        timeout_seconds: int = 60,
        poll_interval_seconds: float = 1.0
    ) -> Optional[Report]:
        """
        리포트 완료 대기

        Args:
            report_id: 리포트 ID
            timeout_seconds: 최대 대기 시간 (초)
            poll_interval_seconds: 폴링 간격 (초)

        Returns:
            Report: 완료된 리포트 또는 None (타임아웃)

        Raises:
            ReportNotFoundError: 리포트를 찾을 수 없는 경우
            ReportExpiredError: 리포트가 만료된 경우
            ReportServiceError: 리포트 생성 실패 시
        """
        start_time = datetime.utcnow()

        while True:
            try:
                report = await self.get_report(report_id)

                # 완료됨
                if report.status == "completed":
                    return report

                # 실패함
                if report.status == "failed":
                    raise ReportServiceError(
                        message=report.error_message or "Report generation failed",
                        code="report_generation_failed"
                    )

                # 처리 중 - 계속 대기

            except (ReportNotFoundError, ReportExpiredError):
                raise

            # 타임아웃 확인
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if elapsed >= timeout_seconds:
                logger.warning("report_wait_timeout", report_id=report_id, timeout=timeout_seconds)
                return None

            await asyncio.sleep(poll_interval_seconds)

    async def create_report_async(
        self,
        username: str,
        background_tasks: Optional[Any] = None
    ) -> str:
        """
        비동기 리포트 생성 (백그라운드 처리)

        Args:
            username: 분석할 인스타그램 사용자명
            background_tasks: FastAPI BackgroundTasks (선택적)

        Returns:
            str: 생성된 리포트 ID
        """
        # 리포트 생성 (processing 상태)
        report = Report(
            username=username,
            status="processing"
        )
        await self.storage.save_report(report)

        logger.info(
            "report_created_for_async_processing",
            report_id=report.id,
            username=username
        )

        # 백그라운드 태스크로 처리
        if background_tasks:
            from fastapi import BackgroundTasks
            background_tasks.add_task(self._process_report, report.id, username)
        else:
            # 백그라운드 태스크가 없으면 즉시 처리
            asyncio.create_task(self._process_report(report.id, username))

        return report.id

    async def _process_report(self, report_id: str, username: str):
        """백그라운드에서 리포트 처리"""
        try:
            logger.info("starting_background_report_processing", report_id=report_id, username=username)

            # 인스타그램 데이터 수집
            instagram_data = await self.instagram_service.fetch_full_data(
                username=username,
                posts_limit=20,
                use_cache=True
            )

            # AI 분석 수행
            analysis_result = await self.ai_service.analyze_profile(instagram_data)

            # 리포트 업데이트
            report = await self.storage.get_report(report_id)
            if report:
                basic_metrics = analysis_result.get("basic_metrics", {})
                # 프로필 정보도 basic_metrics에 저장
                basic_metrics["followers"] = instagram_data.profile.followers
                basic_metrics["following"] = instagram_data.profile.following
                basic_metrics["full_name"] = instagram_data.profile.full_name
                basic_metrics["biography"] = instagram_data.profile.biography
                basic_metrics["is_verified"] = instagram_data.profile.is_verified
                report.basic_metrics = basic_metrics
                report.content_tendency = analysis_result.get("content_tendency", {})
                report.lifestyle = analysis_result.get("lifestyle", {})
                report.personality = analysis_result.get("personality", {})
                report.network = analysis_result.get("network", {})
                report.growth_potential = analysis_result.get("growth_potential", {})
                report.summary = analysis_result.get("summary", "")
                report.profile_image_url = instagram_data.profile.profile_pic_url
                report.profile_image_base64 = instagram_data.profile.profile_pic_base64
                report.collected_posts_count = len(instagram_data.posts)
                report.status = "completed"

                await self.storage.save_report(report)

            logger.info("background_report_processing_completed", report_id=report_id)

            # 분석 완료 트래킹
            await analytics_service.track_analysis_complete(
                report_id=report_id,
                username=username,
                metadata={
                    "posts_count": len(instagram_data.posts),
                    "followers": instagram_data.profile.followers,
                },
            )

        except Exception as e:
            logger.error("background_report_processing_failed", report_id=report_id, error=str(e))
            user_msg = _get_user_friendly_error_message(e)
            await self._mark_report_failed(report_id, user_msg)
            # 분석 실패 트래킹
            await analytics_service.track_analysis_failed(
                report_id=report_id,
                username=username,
                error_message=user_msg,
            )


# 싱글톤 인스턴스
report_service = ReportService()

"""
리포트 생성 라우터
분석 리포트 조회 및 관리 API
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Body
from app.utils.logger import get_logger

logger = get_logger("report_router")

from app.models.schemas import (
    ReportResponse,
    ReportData,
    AnalysisStatus,
    InstagramProfile,
    AnalysisMetrics,
    AIInsight,
    ErrorResponse,
)
from app.models.report import Report
from app.config import get_settings
from app.services.report_service import report_service
from app.utils.exceptions import (
    ReportServiceError,
    ReportNotFoundError,
    ReportExpiredError,
)
from app.services.storage_service import ReportExpiredError as StorageExpiredError
from app.services.analytics_service import analytics_service

router = APIRouter()


@router.get(
    "/report/by-username/{username}",
    responses={
        200: {"description": "리포트 데이터"},
        404: {"model": ErrorResponse, "description": "캐시된 리포트 없음"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="username으로 리포트 조회",
    description="username으로 캐시된 완료 리포트를 조회합니다. 7일 이내 분석 이력이 있으면 report_id와 데이터를 반환합니다.",
)
async def get_report_by_username(username: str) -> dict:
    """
    username으로 기존 완료 리포트를 조회합니다.

    Returns:
        dict: 리포트 데이터 (found=True) 또는 404

    Example:
        GET /api/v1/report/by-username/doto.ri_
    """
    try:
        report_id = await report_service.storage.get_report_id_by_username(username.lower())

        if not report_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No cached report found for '{username}'",
            )

        report = await report_service.get_report(report_id)

        if not report or report.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No completed report found for '{username}'",
            )

        data = report.model_dump()
        data["created_at"] = report.created_at.isoformat()
        data["expires_at"] = report.expires_at.isoformat()
        return data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report: {str(e)}",
        )


@router.get(
    "/report/{report_id}",
    responses={
        404: {"model": ErrorResponse, "description": "Report not found"},
        410: {"model": ErrorResponse, "description": "Report has expired"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
    summary="분석 리포트 조회",
    description="특정 리포트 ID로 완성된 분석 리포트를 조회합니다. 리포트는 생성 후 7일 동안 유효합니다.",
)
async def get_report(report_id: str) -> dict:
    """
    완성된 분석 리포트를 조회합니다.

    Args:
        report_id: 리포트 고유 ID

    Returns:
        dict: 리포트 데이터 (Report 모델 형식)

    Raises:
        HTTPException: 리포트를 찾을 수 없거나 만료된 경우
    """
    try:
        report = await report_service.get_report(report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report '{report_id}' not found",
            )

        # 실패한 경우: error_message를 포함하여 프론트엔드가 처리할 수 있게 반환
        if report.status == "failed":
            return {
                "id": report.id,
                "username": report.username,
                "status": "failed",
                "error_message": report.error_message,
                "created_at": report.created_at.isoformat(),
                "expires_at": report.expires_at.isoformat(),
                "basic_metrics": {},
                "content_tendency": {},
                "lifestyle": {},
                "personality": {},
                "network": {},
                "growth_potential": {},
                "summary": "",
                "profile_image_url": "",
                "collected_posts_count": 0,
            }

        # Report 모델을 직접 반환 (프론트엔드 타입과 일치)
        data = report.model_dump()
        # datetime 직렬화
        data["created_at"] = report.created_at.isoformat()
        data["expires_at"] = report.expires_at.isoformat()
        return data

    except ReportExpiredError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=f"Report '{report_id}' has expired. Please create a new analysis.",
        )

    except ReportNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve report: {str(e)}",
        )


@router.get(
    "/report/{report_id}/status",
    summary="리포트 상태 조회",
    description="리포트의 현재 처리 상태를 조회합니다.",
)
async def get_report_status(report_id: str) -> dict:
    """
    리포트 상태를 조회합니다.

    Args:
        report_id: 리포트 ID

    Returns:
        dict: 리포트 상태 정보
    """
    try:
        status_info = await report_service.get_report_status(report_id)
        return status_info

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report status: {str(e)}",
        )


@router.get(
    "/report/{report_id}/download",
    summary="리포트 이미지 다운로드",
    description="리포트 이미지를 PNG 또는 JPG 형식으로 다운로드합니다. 생성된 이미지는 캐시에서 재사용됩니다.",
    responses={
        200: {"description": "이미지 파일", "content": {"image/png": {}, "image/jpeg": {}}},
        404: {"model": ErrorResponse, "description": "리포트를 찾을 수 없음"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        410: {"model": ErrorResponse, "description": "리포트가 만료됨"},
        500: {"model": ErrorResponse, "description": "이미지 생성 실패"},
    },
)
async def download_report(
    report_id: str,
    format: str = "png"  # png 또는 jpg
):
    """
    리포트 이미지를 다운로드 형식으로 반환합니다.

    Args:
        report_id: 리포트 ID
        format: 이미지 형식 (png 또는 jpg)

    Returns:
        StreamingResponse: 이미지 파일

    Raises:
        HTTPException: 리포트를 찾을 수 없거나 이미지 생성 실패 시
    """
    import io
    from fastapi.responses import StreamingResponse

    from app.services.image_service import (
        report_image_service,
        ImageGenerationError,
        TemplateRenderError,
    )

    # 형식 검증
    format = format.lower()
    if format not in ["png", "jpg", "jpeg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid format. Supported formats: png, jpg",
        )

    try:
        # 저장소에서 리포트 조회
        report = await report_service.get_report(report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report '{report_id}' not found",
            )

        # 처리 중인 경우
        if report.status == "processing":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report is still being processed. Please try again later.",
            )

        # 실패한 경우
        if report.status == "failed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=report.error_message or "Report generation failed",
            )

        # 이미지 생성 (캐시 활용)
        image_bytes = await report_image_service.generate_report_image(report)

        # JPG 포맷 변환 (요청된 경우)
        if format in ["jpg", "jpeg"]:
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(image_bytes))
                # RGBA를 RGB로 변환 (JPG는 투명도 지원 안함)
                if img.mode in ("RGBA", "LA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    if img.mode == "P":
                        img = img.convert("RGBA")
                    if img.mode in ("RGBA", "LA"):
                        background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                        img = background
                    else:
                        img = img.convert("RGB")
                else:
                    img = img.convert("RGB")

                output = io.BytesIO()
                img.save(output, format="JPEG", quality=95)
                image_bytes = output.getvalue()
                media_type = "image/jpeg"
                ext = "jpg"
            except ImportError:
                logger.warning("pillow_not_installed", message="PIL/Pillow not installed, returning PNG")
                media_type = "image/png"
                ext = "png"
            except Exception as e:
                logger.error("jpg_conversion_error", error=str(e))
                media_type = "image/png"
                ext = "png"
        else:
            media_type = "image/png"
            ext = "png"

        filename = f"itsmegram_{report.username}_report.{ext}"

        # 다운로드 트래킹
        await analytics_service.track_download(
            report_id=report_id,
            format=format,
            username=report.username,
        )

        # 스트리밍 응답 반환 (attachment로 설정, CDN 캐싱 헤더 포함)
        return StreamingResponse(
            io.BytesIO(image_bytes),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "public, max-age=3600, immutable",
                "ETag": f'"{report_id}"',
                "Vary": "Accept-Encoding",
            }
        )

    except HTTPException:
        raise
    except ReportNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found",
        )
    except ReportExpiredError:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=f"Report '{report_id}' has expired. Please create a new analysis.",
        )
    except TemplateRenderError as e:
        logger.error("template_render_error", report_id=report_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to render report template: {str(e)}",
        )
    except ImageGenerationError as e:
        logger.error("image_generation_error", report_id=report_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report image: {str(e)}",
        )
    except Exception as e:
        logger.error("unexpected_error", report_id=report_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.get(
    "/report/{report_id}/image",
    summary="리포트 이미지 조회",
    description="리포트 이미지를 생성하여 PNG 형식으로 반환합니다. 생성된 이미지는 1시간 동안 캐싱됩니다.",
    responses={
        200: {"description": "PNG 이미지 바이트", "content": {"image/png": {}}},
        404: {"model": ErrorResponse, "description": "리포트를 찾을 수 없음"},
        410: {"model": ErrorResponse, "description": "리포트가 만료됨"},
        500: {"model": ErrorResponse, "description": "이미지 생성 실패"},
    },
)
async def get_report_image(report_id: str):
    """
    리포트 이미지를 생성하여 반환합니다.

    Args:
        report_id: 리포트 ID

    Returns:
        StreamingResponse: PNG 이미지

    Raises:
        HTTPException: 리포트를 찾을 수 없거나 이미지 생성 실패 시
    """
    import io
    from fastapi.responses import StreamingResponse

    from app.services.image_service import (
        report_image_service,
        ImageGenerationError,
        TemplateRenderError,
    )

    try:
        # 저장소에서 리포트 조회
        report = await report_service.get_report(report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report '{report_id}' not found",
            )

        # 처리 중인 경우
        if report.status == "processing":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Report is still being processed. Please try again later.",
            )

        # 실패한 경우
        if report.status == "failed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=report.error_message or "Report generation failed",
            )

        # 이미지 생성
        image_bytes = await report_image_service.generate_report_image(report)

        # 스트리밍 응답 반환 (CDN 캐싱 헤더 포함)
        return StreamingResponse(
            io.BytesIO(image_bytes),
            media_type="image/png",
            headers={
                "Content-Disposition": f'inline; filename="report_{report.username}_{report_id}.png"',
                "Cache-Control": "public, max-age=3600, immutable",
                "ETag": f'"{report_id}"',
                "Vary": "Accept-Encoding",
            }
        )

    except HTTPException:
        raise
    except TemplateRenderError as e:
        logger.error("template_render_error", report_id=report_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to render report template: {str(e)}",
        )
    except ImageGenerationError as e:
        logger.error("image_generation_error", report_id=report_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report image: {str(e)}",
        )
    except Exception as e:
        logger.error("unexpected_error", report_id=report_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}",
        )


@router.delete(
    "/report/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Report not found"},
    },
    summary="리포트 삭제",
    description="특정 리포트를 삭제합니다.",
)
async def delete_report(report_id: str):
    """
    리포트를 삭제합니다.

    Args:
        report_id: 삭제할 리포트 ID

    Raises:
        HTTPException: 리포트를 찾을 수 없는 경우
    """
    try:
        result = await report_service.delete_report(report_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report '{report_id}' not found",
            )

        return None

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete report: {str(e)}",
        )


@router.get(
    "/reports",
    summary="리포트 목록 조회",
    description="모든 리포트 목록을 조회합니다 (테스트용).",
)
async def list_reports() -> dict:
    """
    저장된 모든 리포트 목록을 조회합니다.

    Returns:
        dict: 리포트 목록
    """
    # TODO: 실제 저장소에서 모든 리포트 조회 구현
    # 현재는 빈 목록 반환
    return {
        "reports": [],
        "total_count": 0,
        "message": "Report listing not fully implemented yet",
    }


@router.post(
    "/report/{report_id}/share",
    summary="리포트 공유 트래킹",
    description="리포트 공유 이벤트를 트래킹합니다. 플랫폼별 공유 횟수를 수집합니다.",
    responses={
        200: {"description": "공유 이벤트 기록 성공"},
        404: {"model": ErrorResponse, "description": "리포트를 찾을 수 없음"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
)
async def track_share(
    report_id: str,
    platform: str = Body(..., embed=True),
) -> dict:
    """
    리포트 공유 이벤트를 트래킹합니다.

    Args:
        report_id: 리포트 ID
        platform: 공유 플랫폼 (instagram, twitter, facebook, native, download 등)

    Returns:
        dict: 트래킹 결과
    """
    try:
        # 리포트 존재 여부 확인
        report = await report_service.get_report(report_id)

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report '{report_id}' not found",
            )

        # 공유 이벤트 로깅
        logger.info(
            "report_shared",
            report_id=report_id,
            platform=platform,
            username=report.username,
            timestamp=datetime.now().isoformat(),
        )

        # Analytics 서비스에 공유 트래킹
        await analytics_service.track_share(
            report_id=report_id,
            platform=platform,
            username=report.username,
        )

        return {
            "success": True,
            "report_id": report_id,
            "platform": platform,
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("share_tracking_error", report_id=report_id, error=str(e))
        # 트래킹 실패는 사용자에게 영향을 주지 않도록 200 반환
        return {
            "success": False,
            "error": str(e),
            "message": "Tracking failed but share was successful",
        }

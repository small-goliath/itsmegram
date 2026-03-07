"""
Analytics 대시보드 라우터
분석 완료율 및 통계 API
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Query, HTTPException, status

from app.models.schemas import ErrorResponse
from app.services.analytics_service import analytics_service, EventType
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger("analytics_router")


@router.get(
    "/analytics/dashboard",
    summary="대시보드 통계 조회",
    description="전체 분석 통계 및 완료율, 공유율 등의 대시보드 데이터를 조회합니다.",
    responses={
        200: {"description": "대시보드 통계 데이터"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
)
async def get_dashboard():
    """
    대시보드 통계 데이터를 조회합니다.

    Returns:
        dict: 대시보드 통계 데이터
    """
    try:
        dashboard_data = analytics_service.get_dashboard_data()
        logger.info("dashboard_data_requested")
        return dashboard_data

    except Exception as e:
        logger.error("dashboard_data_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}",
        )


@router.get(
    "/analytics/stats",
    summary="통계 조회",
    description="특정 기간의 통계 데이터를 조회합니다.",
    responses={
        200: {"description": "통계 데이터"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
)
async def get_stats(
    start_date: Optional[str] = Query(
        None,
        description="시작 날짜 (ISO 8601 형식: YYYY-MM-DD)",
        example="2024-01-01",
    ),
    end_date: Optional[str] = Query(
        None,
        description="종료 날짜 (ISO 8601 형식: YYYY-MM-DD)",
        example="2024-12-31",
    ),
):
    """
    특정 기간의 통계 데이터를 조회합니다.

    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)

    Returns:
        dict: 통계 데이터
    """
    try:
        # 날짜 파싱
        start_time = None
        end_time = None

        if start_date:
            try:
                start_time = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD",
                )

        if end_date:
            try:
                # 종료 날짜는 해당 일의 끝으로 설정
                end_time = datetime.strptime(end_date, "%Y-%m-%d")
                end_time = end_time.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD",
                )

        stats = analytics_service.get_stats(start_time, end_time)
        logger.info(
            "stats_requested",
            start_date=start_date,
            end_date=end_date,
        )
        return stats

    except HTTPException:
        raise
    except Exception as e:
        logger.error("stats_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}",
        )


@router.get(
    "/analytics/events",
    summary="이벤트 로그 조회",
    description="이벤트 로그를 조회합니다. 개인정보 보호를 위해 username과 IP는 해시되어 저장됩니다.",
    responses={
        200: {"description": "이벤트 로그 목록"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
)
async def get_events(
    event_type: Optional[str] = Query(
        None,
        description="이벤트 타입 필터",
        example="analysis_complete",
    ),
    start_date: Optional[str] = Query(
        None,
        description="시작 날짜 (ISO 8601 형식: YYYY-MM-DD)",
        example="2024-01-01",
    ),
    end_date: Optional[str] = Query(
        None,
        description="종료 날짜 (ISO 8601 형식: YYYY-MM-DD)",
        example="2024-12-31",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="최대 조회 개수",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="오프셋",
    ),
):
    """
    이벤트 로그를 조회합니다.

    Args:
        event_type: 이벤트 타입 필터
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        limit: 최대 조회 개수
        offset: 오프셋

    Returns:
        dict: 이벤트 로그 목록
    """
    try:
        # 이벤트 타입 검증
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = EventType(event_type)
            except ValueError:
                valid_types = [e.value for e in EventType]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid event_type. Valid types: {', '.join(valid_types)}",
                )

        # 날짜 파싱
        start_time = None
        end_time = None

        if start_date:
            try:
                start_time = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD",
                )

        if end_date:
            try:
                end_time = datetime.strptime(end_date, "%Y-%m-%d")
                end_time = end_time.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD",
                )

        events = analytics_service.get_events(
            start_time=start_time,
            end_time=end_time,
            event_type=event_type_enum,
            limit=limit,
            offset=offset,
        )

        logger.info(
            "events_requested",
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
            result_count=len(events),
        )

        return {
            "events": events,
            "total_count": len(events),
            "limit": limit,
            "offset": offset,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("events_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get events: {str(e)}",
        )


@router.get(
    "/analytics/completion-rate",
    summary="분석 완료율 조회",
    description="분석 완료율을 조회합니다.",
    responses={
        200: {"description": "완료율 데이터"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
)
async def get_completion_rate(
    start_date: Optional[str] = Query(
        None,
        description="시작 날짜 (ISO 8601 형식: YYYY-MM-DD)",
        example="2024-01-01",
    ),
    end_date: Optional[str] = Query(
        None,
        description="종료 날짜 (ISO 8601 형식: YYYY-MM-DD)",
        example="2024-12-31",
    ),
):
    """
    분석 완료율을 조회합니다.

    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)

    Returns:
        dict: 완료율 데이터
    """
    try:
        # 날짜 파싱
        start_time = None
        end_time = None

        if start_date:
            try:
                start_time = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD",
                )

        if end_date:
            try:
                end_time = datetime.strptime(end_date, "%Y-%m-%d")
                end_time = end_time.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD",
                )

        completion_rate = analytics_service.get_completion_rate(start_time, end_time)
        avg_duration = analytics_service.get_avg_duration(start_time, end_time)

        return {
            "completion_rate": completion_rate,
            "completion_percentage": round(completion_rate * 100, 2),
            "avg_duration_ms": avg_duration,
            "avg_duration_seconds": round(avg_duration / 1000, 2) if avg_duration else None,
            "start_date": start_date,
            "end_date": end_date,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("completion_rate_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get completion rate: {str(e)}",
        )


@router.get(
    "/analytics/share-rate",
    summary="공유율 조회",
    description="공유율을 조회합니다.",
    responses={
        200: {"description": "공유율 데이터"},
        400: {"model": ErrorResponse, "description": "잘못된 요청"},
        500: {"model": ErrorResponse, "description": "서버 오류"},
    },
)
async def get_share_rate(
    start_date: Optional[str] = Query(
        None,
        description="시작 날짜 (ISO 8601 형식: YYYY-MM-DD)",
        example="2024-01-01",
    ),
    end_date: Optional[str] = Query(
        None,
        description="종료 날짜 (ISO 8601 형식: YYYY-MM-DD)",
        example="2024-12-31",
    ),
):
    """
    공유율을 조회합니다.

    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)

    Returns:
        dict: 공유율 데이터
    """
    try:
        # 날짜 파싱
        start_time = None
        end_time = None

        if start_date:
            try:
                start_time = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD",
                )

        if end_date:
            try:
                end_time = datetime.strptime(end_date, "%Y-%m-%d")
                end_time = end_time.replace(hour=23, minute=59, second=59)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD",
                )

        share_rate = analytics_service.get_share_rate(start_time, end_time)

        return {
            "share_rate": share_rate,
            "share_percentage": round(share_rate * 100, 2),
            "start_date": start_date,
            "end_date": end_date,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("share_rate_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get share rate: {str(e)}",
        )

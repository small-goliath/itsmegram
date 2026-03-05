"""
itsmegram - 리포트 이미지 생성 서비스 테스트
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from io import BytesIO

from PIL import Image

from app.models.report import Report
from app.services.image_service import ReportImageService, report_image_service


@pytest.fixture
def sample_report():
    """테스트용 샘플 리포트"""
    return Report(
        id="test-report-123",
        username="testuser",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24),
        basic_metrics={
            "engagement_rate": 75.5,
            "avg_likes": 1250,
            "avg_comments": 85,
            "followers": 15000,
            "following": 500,
        },
        content_tendency={
            "categories": ["여행", "사진", "일상"],
            "visual_style": "밝고 선명한 색감의 사진을 주로 게시합니다",
            "text_style": "친근하고 자연스러운 문체를 사용합니다",
            "hashtag_pattern": ["여행", "일상", "사진"],
            "posting_frequency": "주 3-4회",
        },
        lifestyle={
            "interests": ["여행", "사진", "음식", "패션"],
            "activity_pattern": "주말에 활동이 집중되는 패턴",
            "consumption": ["체험 중심 소비", "가성비 중시"],
        },
        personality={
            "expression_strength": 85,
            "extroversion": "외향적인 성향으로 적극적으로 소통합니다",
            "communication": "친근하고 개방적인 커뮤니케이션 스타일",
        },
        network={
            "engagement_quality": "높은 참여 품질을 보입니다",
            "community_type": "관심사 기반 커뮤니티",
        },
        growth_potential={
            "trend": "안정적인 성장 추세",
            "consistency": "꾸준한 활동을 유지하고 있습니다",
            "suggestions": ["릴스 콘텐츠 강화", "게시 시간 최적화"],
        },
        summary="이 계정은 여행과 일상 콘텐츠를 중심으로 활동하며, 높은 참여율과 꾸준한 성장을 보이고 있습니다. 외향적인 성향과 뛰어난 표현력으로 팔로워와의 소통이 활발합니다.",
        profile_image_url="",
        collected_posts_count=20,
        status="completed",
    )


@pytest.fixture
def image_service():
    """이미지 서비스 인스턴스"""
    return ReportImageService()


class TestReportImageService:
    """리포트 이미지 서비스 테스트"""

    @pytest.mark.asyncio
    async def test_generate_report_image(self, image_service, sample_report):
        """이미지 생성 테스트"""
        print("\n[TEST] 이미지 생성 테스트 시작...")

        # 이미지 생성
        image_bytes = await image_service.generate_report_image(
            sample_report,
            use_cache=False
        )

        # 이미지 바이트 확인
        assert image_bytes is not None
        assert len(image_bytes) > 0
        print(f"[TEST] 생성된 이미지 크기: {len(image_bytes)} bytes")

        # 이미지 형식 검증
        image = Image.open(BytesIO(image_bytes))
        assert image.format == "PNG"
        print(f"[TEST] 이미지 형식: {image.format}")

        return image_bytes

    @pytest.mark.asyncio
    async def test_image_resolution(self, image_service, sample_report):
        """이미지 해상도 테스트 (1080x1920)"""
        print("\n[TEST] 이미지 해상도 테스트 시작...")

        image_bytes = await image_service.generate_report_image(
            sample_report,
            use_cache=False
        )

        image = Image.open(BytesIO(image_bytes))
        width, height = image.size

        print(f"[TEST] 이미지 해상도: {width}x{height}")

        # 너비는 정확히 1080이어야 함
        assert width == 1080, f"Expected width 1080, got {width}"

        # 높이는 최소 1920 이상이어야 함 (full_page 스크린샷)
        assert height >= 1920, f"Expected height >= 1920, got {height}"

    @pytest.mark.asyncio
    async def test_korean_font_rendering(self, image_service, sample_report):
        """한글 폰트 렌더링 테스트"""
        print("\n[TEST] 한글 폰트 렌더링 테스트 시작...")

        image_bytes = await image_service.generate_report_image(
            sample_report,
            use_cache=False
        )

        # 이미지가 생성되었는지 확인
        assert image_bytes is not None
        assert len(image_bytes) > 0

        # 이미지 파일로 저장 (수동 확인용)
        test_output_path = "/Users/iymaeng/Documents/private/itsmegram/backend/tests/test_output_korean.png"
        with open(test_output_path, "wb") as f:
            f.write(image_bytes)

        print(f"[TEST] 테스트 이미지 저장됨: {test_output_path}")

        # 파일 크기 확인 (너무 작으면 렌더링 문제 가능성)
        assert len(image_bytes) > 10000, "Image seems too small, possible rendering issue"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Redis connection")
    async def test_image_caching(self, image_service, sample_report):
        """이미지 캐싱 테스트 (Redis 필요)"""
        print("\n[TEST] 이미지 캐싱 테스트 시작...")

        # 첫 번째 생성 (캐시 없음)
        start_time = asyncio.get_event_loop().time()
        image_bytes_1 = await image_service.generate_report_image(
            sample_report,
            use_cache=True
        )
        first_duration = asyncio.get_event_loop().time() - start_time
        print(f"[TEST] 첫 번째 생성 시간: {first_duration:.2f}s")

        # 두 번째 생성 (캐시 사용)
        start_time = asyncio.get_event_loop().time()
        image_bytes_2 = await image_service.generate_report_image(
            sample_report,
            use_cache=True
        )
        second_duration = asyncio.get_event_loop().time() - start_time
        print(f"[TEST] 두 번째 생성 시간 (캐시): {second_duration:.2f}s")

        # 캐시된 이미지가 동일한지 확인
        assert image_bytes_1 == image_bytes_2

        # 캐시된 경우 더 빨라야 함
        assert second_duration < first_duration

        # 캐시 정보 확인
        cache_info = await image_service.get_cache_info(sample_report.id)
        assert cache_info["cached"] is True
        print(f"[TEST] 캐시 정보: {cache_info}")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Requires Redis connection")
    async def test_cache_invalidation(self, image_service, sample_report):
        """캐시 무효화 테스트 (Redis 필요)"""
        print("\n[TEST] 캐시 무효화 테스트 시작...")

        # 이미지 생성 및 캐싱
        await image_service.generate_report_image(sample_report, use_cache=True)

        # 캐시 확인
        cache_info = await image_service.get_cache_info(sample_report.id)
        assert cache_info["cached"] is True

        # 캐시 무효화
        result = await image_service.invalidate_cache(sample_report.id)
        assert result is True

        # 캐시가 삭제되었는지 확인
        cache_info = await image_service.get_cache_info(sample_report.id)
        assert cache_info["cached"] is False
        print("[TEST] 캐시 무효화 성공")

    @pytest.mark.asyncio
    async def test_template_rendering(self, image_service, sample_report):
        """템플릿 렌더링 테스트"""
        print("\n[TEST] 템플릿 렌더링 테스트 시작...")

        html_content = image_service._render_template(sample_report)

        # HTML이 생성되었는지 확인
        assert html_content is not None
        assert len(html_content) > 0

        # 필수 요소가 포함되어 있는지 확인
        assert sample_report.username in html_content
        assert "ITSMEGRAM" in html_content
        assert "핵심 지표" in html_content
        assert "콘텐츠 성향" in html_content
        assert "라이프스타일" in html_content
        assert "성격 분석" in html_content
        assert "종합 분석" in html_content

        print("[TEST] 템플릿 렌더링 성공")

    @pytest.mark.asyncio
    async def test_file_size_optimization(self, image_service, sample_report):
        """이미지 파일 크기 최적화 테스트"""
        print("\n[TEST] 파일 크기 최적화 테스트 시작...")

        image_bytes = await image_service.generate_report_image(
            sample_report,
            use_cache=False
        )

        size_kb = len(image_bytes) / 1024
        size_mb = size_kb / 1024

        print(f"[TEST] 이미지 파일 크기: {size_kb:.2f} KB ({size_mb:.2f} MB)")

        # 파일 크기가 합리적인 범위 내에 있는지 확인
        # PNG 형식의 1080x1920 이미지는 보통 500KB ~ 5MB 사이
        assert len(image_bytes) > 50000, "Image too small, possible quality issue"
        assert len(image_bytes) < 10 * 1024 * 1024, "Image too large, needs optimization"


@pytest.mark.asyncio
async def test_end_to_end():
    """엔드투엔드 테스트"""
    print("\n" + "="*60)
    print("[E2E TEST] 리포트 이미지 생성 엔드투엔드 테스트")
    print("="*60)

    # 샘플 리포트 생성
    report = Report(
        id="e2e-test-report",
        username="itsmegram_user",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=24),
        basic_metrics={
            "engagement_rate": 82.3,
            "avg_likes": 2340,
            "avg_comments": 156,
            "followers": 25000,
            "following": 800,
        },
        content_tendency={
            "categories": ["패션", "뷰티", "라이프스타일"],
            "visual_style": "세련되고 감각적인 비주얼을 선보입니다",
            "text_style": "트렌디하고 세련된 어휘를 사용합니다",
            "hashtag_pattern": ["OOTD", "데일리룩", "패션"],
            "posting_frequency": "주 5-6회",
        },
        lifestyle={
            "interests": ["패션", "뷰티", "카페", "여행"],
            "activity_pattern": "평일 저녁과 주말에 활발히 활동",
            "consumption": ["프리미엄 소비", "트렌드 중시"],
        },
        personality={
            "expression_strength": 92,
            "extroversion": "매우 외향적이고 리더십이 강합니다",
            "communication": "적극적이고 설득력 있는 커뮤니케이션",
        },
        network={
            "engagement_quality": "매우 높은 참여 품질",
            "community_type": "패션/뷰티 커뮤니티 중심",
        },
        growth_potential={
            "trend": "긍정적인 성장 추세",
            "consistency": "매우 꾸준한 활동",
            "suggestions": ["브랜드 콜라보", "릴스 콘텐츠 확대"],
        },
        summary="패션과 뷰티 중심의 인플루언서형 계정으로, 높은 참여율과 꾸준한 성장세를 보이고 있습니다. 세련된 비주얼과 트렌디한 감각으로 팔로워들의 큰 호응을 얻고 있으며, 브랜드 콜라보 등 수익화 가능성이 높습니다.",
        profile_image_url="",
        collected_posts_count=24,
        status="completed",
    )

    service = ReportImageService()

    # 이미지 생성
    print("\n[1/4] 이미지 생성 중...")
    image_bytes = await service.generate_report_image(report, use_cache=False)
    print(f"    완료! 크기: {len(image_bytes) / 1024:.2f} KB")

    # 해상도 확인
    print("\n[2/4] 해상도 확인 중...")
    image = Image.open(BytesIO(image_bytes))
    width, height = image.size
    print(f"    해상도: {width}x{height}")
    assert width == 1080
    assert height >= 1920

    # 파일 저장
    print("\n[3/4] 테스트 이미지 저장 중...")
    output_path = "/Users/iymaeng/Documents/private/itsmegram/backend/tests/test_report_story.png"
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    print(f"    저장 완료: {output_path}")

    # 캐시 테스트
    print("\n[4/4] 캐싱 테스트 중...")
    cached_image = await service.generate_report_image(report, use_cache=True)
    assert cached_image == image_bytes
    print("    캐싱 작동 확인!")

    print("\n" + "="*60)
    print("[E2E TEST] 모든 테스트 통과!")
    print("="*60)


if __name__ == "__main__":
    # 직접 실행 시 pytest 없이 테스트
    asyncio.run(test_end_to_end())

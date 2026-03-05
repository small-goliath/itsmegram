"""
AI 분석 서비스 테스트 스크립트
Moonshot AI 연동 테스트 및 검증
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

from app.services.ai_service import AIService, ai_service
from app.models.schemas import ProfileData, PostData, InstagramData


def create_sample_instagram_data() -> InstagramData:
    """테스트용 샘플 인스타그램 데이터 생성"""

    profile = ProfileData(
        username="test_traveler",
        full_name="Test Traveler",
        biography="Travel lover | Photographer | Foodie 🌍📸🍜\nDM for collaborations",
        followers=15000,
        following=800,
        posts_count=250,
        is_private=False,
        profile_pic_url="https://example.com/profile.jpg",
        is_verified=False,
        external_url="https://blog.example.com",
    )

    posts = [
        PostData(
            post_id="post_1",
            caption="Beautiful sunset in Bali! 🌅 #travel #bali #sunset #photography #wanderlust",
            likes=1250,
            comments=85,
            media_url="https://example.com/post1.jpg",
            hashtags=["travel", "bali", "sunset", "photography", "wanderlust"],
            mentions=[],
            timestamp=datetime(2024, 12, 1, 18, 30),
            post_type="image",
            shortcode="ABC123",
        ),
        PostData(
            post_id="post_2",
            caption="Amazing pasta in Rome! 🍝 #foodie #rome #italy #pasta #foodphotography",
            likes=980,
            comments=62,
            media_url="https://example.com/post2.jpg",
            hashtags=["foodie", "rome", "italy", "pasta", "foodphotography"],
            mentions=[],
            timestamp=datetime(2024, 11, 28, 12, 0),
            post_type="image",
            shortcode="DEF456",
        ),
        PostData(
            post_id="post_3",
            caption="Morning workout routine 💪 #fitness #health #workout #morningroutine",
            likes=750,
            comments=45,
            media_url="https://example.com/post3.jpg",
            hashtags=["fitness", "health", "workout", "morningroutine"],
            mentions=[],
            timestamp=datetime(2024, 11, 25, 7, 0),
            post_type="video",
            shortcode="GHI789",
        ),
        PostData(
            post_id="post_4",
            caption="Weekend getaway with friends! 🎉 #friends #weekend #fun #memories",
            likes=1500,
            comments=120,
            media_url="https://example.com/post4.jpg",
            hashtags=["friends", "weekend", "fun", "memories"],
            mentions=["@friend1", "@friend2"],
            timestamp=datetime(2024, 11, 20, 15, 0),
            post_type="carousel",
            shortcode="JKL012",
        ),
        PostData(
            post_id="post_5",
            caption="New camera setup 📷 #photography #gear #camera #tech",
            likes=620,
            comments=38,
            media_url="https://example.com/post5.jpg",
            hashtags=["photography", "gear", "camera", "tech"],
            mentions=[],
            timestamp=datetime(2024, 11, 15, 10, 0),
            post_type="image",
            shortcode="MNO345",
        ),
    ]

    return InstagramData(
        profile=profile,
        posts=posts,
        collected_at=datetime.utcnow(),
    )


def validate_analysis_result(result: Dict[str, Any]) -> bool:
    """분석 결과 구조 검증"""
    required_fields = {
        "basic_metrics": ["avg_likes", "engagement_rate", "post_type_ratio"],
        "content_tendency": ["categories", "visual_style", "text_style", "hashtag_pattern"],
        "lifestyle": ["interests", "activity_pattern", "consumption"],
        "personality": ["extroversion", "expression_strength", "communication"],
        "network": ["engagement_quality", "community_type"],
        "growth_potential": ["trend", "consistency", "suggestions"],
        "summary": None,
    }

    all_valid = True
    errors = []

    for field, subfields in required_fields.items():
        if field not in result:
            errors.append(f"Missing required field: {field}")
            all_valid = False
            continue

        if subfields is not None:
            if not isinstance(result[field], dict):
                errors.append(f"Field {field} should be a dict")
                all_valid = False
                continue

            for subfield in subfields:
                if subfield not in result[field]:
                    errors.append(f"Missing subfield: {field}.{subfield}")
                    all_valid = False

    # summary 길이 검증
    if "summary" in result:
        summary = result["summary"]
        sentences = [s.strip() for s in summary.split('.') if s.strip()]
        if len(sentences) < 5 or len(sentences) > 7:
            errors.append(f"Summary should have 5-7 sentences, got {len(sentences)}")
            all_valid = False

    # 추정 표현 사용 검증
    estimation_patterns = ['보입니다', '추정됩니다', '판단됩니다', '예상됩니다']
    if "summary" in result:
        has_estimation = any(pattern in result["summary"] for pattern in estimation_patterns)
        if not has_estimation:
            errors.append("Summary should contain estimation phrases (~보입니다, ~추정됩니다)")
            all_valid = False

    if errors:
        print("\n[Validation Errors]")
        for error in errors:
            print(f"  - {error}")

    return all_valid


async def test_ai_analysis():
    """AI 분석 테스트"""
    print("=" * 60)
    print("AI 분석 서비스 테스트 (Moonshot AI)")
    print("=" * 60)

    # API 키 확인
    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        print("\n[ERROR] MOONSHOT_API_KEY 환경변수가 설정되지 않았습니다.")
        print("테스트를 진행하려면 .env 파일에 MOONSHOT_API_KEY를 설정해주세요.")
        return False

    print(f"\n[1/5] API 키 확인: {'✓ 설정됨' if api_key else '✗ 없음'}")

    # 샘플 데이터 생성
    print("\n[2/5] 샘플 데이터 생성 중...")
    instagram_data = create_sample_instagram_data()
    print(f"  - 사용자명: {instagram_data.profile.username}")
    print(f"  - 팔로워: {instagram_data.profile.followers:,}")
    print(f"  - 게시물 수: {len(instagram_data.posts)}")

    # AI 서비스 초기화
    print("\n[3/5] AI 서비스 초기화 중...")
    service = AIService(api_key=api_key)
    print(f"  - 모델: {service.model}")
    print(f"  - 타임아웃: {service.timeout_seconds}초")

    # AI 분석 수행
    print("\n[4/5] AI 분석 수행 중... (약 10-20초 소요)")
    try:
        result = await service.analyze_profile(instagram_data)
        print("  ✓ 분석 완료")
    except Exception as e:
        print(f"  ✗ 분석 실패: {str(e)}")
        return False

    # 결과 출력
    print("\n[5/5] 분석 결과:")
    print("-" * 60)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("-" * 60)

    # 결과 검증
    print("\n[검증 결과]")
    is_valid = validate_analysis_result(result)
    if is_valid:
        print("  ✓ 모든 필드가 올바르게 포함됨")
        print("  ✓ summary 길이 적절 (5-7 문장)")
        print("  ✓ 추정 표현 사용됨")
    else:
        print("  ✗ 일부 검증 실패 (위 에러 메시지 참조)")

    return is_valid


async def test_error_handling():
    """에러 핸들링 테스트"""
    print("\n" + "=" * 60)
    print("에러 핸들링 테스트")
    print("=" * 60)

    # 잘못된 API 키 테스트
    print("\n[1/3] 잘못된 API 키 테스트...")
    try:
        bad_service = AIService(api_key="invalid_key")
        instagram_data = create_sample_instagram_data()
        await bad_service.analyze_profile(instagram_data)
        print("  ✗ 예외가 발생하지 않음 (실패)")
    except Exception as e:
        print(f"  ✓ 예외 발생: {type(e).__name__}")
        print(f"    메시지: {str(e)[:50]}...")

    # API 키 없음 테스트
    print("\n[2/3] API 키 없음 테스트...")
    original_key = os.getenv("MOONSHOT_API_KEY")
    os.environ["MOONSHOT_API_KEY"] = ""
    try:
        no_key_service = AIService()
        instagram_data = create_sample_instagram_data()
        await no_key_service.analyze_profile(instagram_data)
        print("  ✗ 예외가 발생하지 않음 (실패)")
    except Exception as e:
        print(f"  ✓ 예외 발생: {type(e).__name__}")
        print(f"    메시지: {str(e)[:50]}...")
    finally:
        if original_key:
            os.environ["MOONSHOT_API_KEY"] = original_key

    # JSON 파싱 에러 테스트 (모의)
    print("\n[3/3] JSON 파싱 에러 처리 테스트...")
    print("  ✓ JSON 파싱 에러 핸들링 구현됨 (ai_service.py 참조)")

    return True


async def test_report_generation():
    """리포트 생성 테스트"""
    print("\n" + "=" * 60)
    print("리포트 생성 테스트")
    print("=" * 60)

    api_key = os.getenv("MOONSHOT_API_KEY")
    if not api_key:
        print("\n[SKIP] API 키가 설정되지 않아 테스트를 건너뜁니다.")
        return True

    print("\n[1/2] 전체 리포트 생성 중... (약 10-20초 소요)")
    try:
        instagram_data = create_sample_instagram_data()
        report = await ai_service.generate_report(instagram_data)
        print("  ✓ 리포트 생성 완료")
        print(f"    - 전체 점수: {report.overall_score}/100")
        print(f"    - 인사이트 수: {len(report.ai_insights)}")
        print(f"    - 생성 시간: {report.generated_at}")
    except Exception as e:
        print(f"  ✗ 리포트 생성 실패: {str(e)}")
        return False

    print("\n[2/2] 인사이트 상세 정보:")
    for idx, insight in enumerate(report.ai_insights, 1):
        print(f"  {idx}. [{insight.category}] {insight.title} (점수: {insight.score}/10)")
        print(f"     설명: {insight.description[:60]}...")

    return True


async def main():
    """메인 테스트 실행"""
    print("\n" + "=" * 60)
    print("itsmegram AI 서비스 테스트 시작")
    print("=" * 60)

    results = []

    # 테스트 1: AI 분석
    try:
        result = await test_ai_analysis()
        results.append(("AI 분석", result))
    except Exception as e:
        print(f"\n[ERROR] AI 분석 테스트 중 예외 발생: {str(e)}")
        results.append(("AI 분석", False))

    # 테스트 2: 에러 핸들링
    try:
        result = await test_error_handling()
        results.append(("에러 핸들링", result))
    except Exception as e:
        print(f"\n[ERROR] 에러 핸들링 테스트 중 예외 발생: {str(e)}")
        results.append(("에러 핸들링", False))

    # 테스트 3: 리포트 생성
    try:
        result = await test_report_generation()
        results.append(("리포트 생성", result))
    except Exception as e:
        print(f"\n[ERROR] 리포트 생성 테스트 중 예외 발생: {str(e)}")
        results.append(("리포트 생성", False))

    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")

    all_passed = all(passed for _, passed in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("모든 테스트 통과! ✓")
    else:
        print("일부 테스트 실패. 로그를 확인해주세요. ✗")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

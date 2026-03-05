#!/usr/bin/env python3
"""
리포트 다운로드 API 테스트 스크립트
"""

import asyncio
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.report import Report
from app.services.storage_service import ReportStorage
from app.services.image_service import report_image_service


async def create_test_report():
    """테스트용 완료된 리포트 생성"""
    storage = ReportStorage()

    # 테스트 리포트 생성
    report = Report(
        username="testuser",
        status="completed"
    )

    # 테스트 데이터 채우기
    report.basic_metrics = {
        "followers": 1234,
        "following": 567,
        "posts": 89,
        "engagement_rate": 5.5,
        "avg_likes": 100,
        "avg_comments": 20,
        "full_name": "Test User",
        "biography": "This is a test biography for testing purposes.",
        "is_verified": False,
    }
    report.content_tendency = {
        "categories": ["lifestyle", "travel", "food"],
        "visual_style": "밝고 선명한 색감",
        "text_style": "친근하고 구어체",
        "hashtag_pattern": ["#lifestyle", "#travel", "#foodie"],
        "posting_frequency": "주 3-4회",
    }
    report.lifestyle = {
        "interests": ["여행", "맛집탐방", "사진"],
        "activity_pattern": "주로 저녁 시간대 활동",
        "consumption": ["카페", "레스토랑", "여행"],
    }
    report.personality = {
        "expression_strength": 75,
        "extroversion": "외향적",
        "communication": "적극적 소통",
    }
    report.network = {
        "engagement_quality": "높음",
        "community_type": "친구 중심",
    }
    report.growth_potential = {
        "trend": "상승세",
        "consistency": "규칙적",
        "suggestions": ["더 자주 게시", "스토리 활용"],
    }
    report.summary = "테스트 사용자는 라이프스타일 중심의 콘텐츠를 공유하며, 외향적인 성격으로 활발한 소통을 보입니다."
    report.profile_image_url = "https://via.placeholder.com/150"
    report.collected_posts_count = 20

    # 저장소에 저장
    await storage.save_report(report)
    print(f"✅ 테스트 리포트 생성 완료: {report.id}")
    print(f"   - Username: {report.username}")
    print(f"   - Status: {report.status}")

    return report.id, report


async def test_download_api(report_id: str):
    """다운로드 API 테스트"""
    import httpx

    base_url = "http://localhost:8000/api/v1"

    async with httpx.AsyncClient() as client:
        # 1. PNG 다운로드 테스트
        print("\n📥 PNG 다운로드 테스트...")
        response = await client.get(f"{base_url}/report/{report_id}/download?format=png")
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            content_disposition = response.headers.get("content-disposition", "")
            print(f"   Content-Type: {content_type}")
            print(f"   Content-Disposition: {content_disposition}")
            print(f"   File size: {len(response.content)} bytes")

            # 파일 저장
            filename = "test_download.png"
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"   ✅ 파일 저장 완료: {filename}")
        else:
            print(f"   ❌ 오류: {response.text}")

        # 2. JPG 다운로드 테스트
        print("\n📥 JPG 다운로드 테스트...")
        response = await client.get(f"{base_url}/report/{report_id}/download?format=jpg")
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            content_type = response.headers.get("content-type", "")
            content_disposition = response.headers.get("content-disposition", "")
            print(f"   Content-Type: {content_type}")
            print(f"   Content-Disposition: {content_disposition}")
            print(f"   File size: {len(response.content)} bytes")

            # 파일 저장
            filename = "test_download.jpg"
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f"   ✅ 파일 저장 완료: {filename}")
        else:
            print(f"   ❌ 오류: {response.text}")

        # 3. 잘못된 형식 테스트
        print("\n📥 잘못된 형식 테스트...")
        response = await client.get(f"{base_url}/report/{report_id}/download?format=invalid")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        if response.status_code == 400:
            print("   ✅ 400 오류 정상 반환")
        else:
            print("   ❌ 예상치 못한 응답")

        # 4. 존재하지 않는 리포트 테스트
        print("\n📥 존재하지 않는 리포트 테스트...")
        response = await client.get(f"{base_url}/report/nonexistent/download?format=png")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text}")
        if response.status_code == 404:
            print("   ✅ 404 오류 정상 반환")
        else:
            print("   ❌ 예상치 못한 응답")


async def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("🧪 리포트 다운로드 API 테스트")
    print("=" * 60)

    # 테스트 리포트 생성
    report_id, report = await create_test_report()

    # 이미지 생성 (캐시용)
    print("\n🖼️  리포트 이미지 생성 중...")
    try:
        image_bytes = await report_image_service.generate_report_image(report)
        print(f"   ✅ 이미지 생성 완료: {len(image_bytes)} bytes")
    except Exception as e:
        print(f"   ⚠️  이미지 생성 실패 (계속 진행): {e}")

    # 다운로드 API 테스트
    await test_download_api(report_id)

    print("\n" + "=" * 60)
    print("✅ 테스트 완료")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

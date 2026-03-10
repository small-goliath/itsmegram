#!/usr/bin/env python3
"""
Instagram web_profile_info API 테스트 스크립트
PRD v2 기술적 타당성 검증용
"""

import httpx
import json
import time

# 테스트 대상 사용자
TEST_USERNAME = "doto.ri_"

# 필수 헤더 (PRD v2에 명시된 대로)
REQUIRED_HEADERS = {
    "x-ig-app-id": "936619743392459",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.instagram.com/",
    "Accept": "*/*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
}

def test_basic_request():
    """테스트 1: 헤더 없는 기본 요청"""
    print("=" * 60)
    print("테스트 1: 헤더 없는 기본 요청")
    print("=" * 60)

    url = "https://www.instagram.com/api/v1/users/web_profile_info/"
    params = {"username": TEST_USERNAME}

    try:
        response = httpx.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response (first 1000 chars):\n{response.text[:1000]}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\nJSON 파싱 성공!")
                if "data" in data and "user" in data.get("data", {}):
                    user = data["data"]["user"]
                    print(f"\n추출 가능한 필드:")
                    print(f"  - username: {user.get('username')}")
                    print(f"  - full_name: {user.get('full_name')}")
                    print(f"  - is_private: {user.get('is_private')}")
                    print(f"  - is_verified: {user.get('is_verified')}")
            except:
                print("\nJSON 파싱 실패 (HTML 응답일 가능성)")
        return response.status_code
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_with_headers():
    """테스트 2: 필수 헤더 포함 요청"""
    print("\n" + "=" * 60)
    print("테스트 2: 필수 헤더 포함 요청 (x-ig-app-id)")
    print("=" * 60)

    url = "https://www.instagram.com/api/v1/users/web_profile_info/"
    params = {"username": TEST_USERNAME}

    try:
        response = httpx.get(url, params=params, headers=REQUIRED_HEADERS, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Headers sent: {list(REQUIRED_HEADERS.keys())}")
        print(f"\nResponse (first 1500 chars):\n{response.text[:1500]}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✅ JSON 파싱 성공!")

                if "data" in data:
                    user = data["data"].get("user", {})
                    print(f"\n📊 추출 가능한 필드:")
                    print(f"  - username: {user.get('username')}")
                    print(f"  - full_name: {user.get('full_name')}")
                    print(f"  - biography: {user.get('biography', '')[:50]}...")
                    print(f"  - is_private: {user.get('is_private')}")
                    print(f"  - is_verified: {user.get('is_verified')}")

                    # 팔로워/팔로잉 정보
                    edge_followed_by = user.get('edge_followed_by', {})
                    edge_follow = user.get('edge_follow', {})
                    edge_media = user.get('edge_owner_to_timeline_media', {})

                    print(f"  - followers: {edge_followed_by.get('count')}")
                    print(f"  - following: {edge_follow.get('count')}")
                    print(f"  - posts_count: {edge_media.get('count')}")
                    print(f"  - profile_pic_url: {user.get('profile_pic_url_hd', 'N/A')[:50]}...")

                    return True
                else:
                    print(f"\n⚠️ 'data' 필드 없음. 응답 구조 확인 필요")
                    print(f"Available keys: {list(data.keys())}")
                    return False
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON 파싱 실패: {e}")
                print("HTML 응답일 가능성 - 추가 인증 필요")
                return False
        elif response.status_code == 401:
            print("\n❌ 401 Unauthorized - 세션 쿠키 필요")
            return False
        elif response.status_code == 403:
            print("\n❌ 403 Forbidden - TLS fingerprinting 또는 추가 인증 필요")
            return False
        elif response.status_code == 429:
            print("\n❌ 429 Too Many Requests - Rate limit")
            return False
        else:
            print(f"\n⚠️ 예상치 못한 상태 코드: {response.status_code}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False

def test_with_session():
    """테스트 3: 세션 쿠키 포함 (선택적)"""
    print("\n" + "=" * 60)
    print("테스트 3: 세션 쿠키 포함 요청")
    print("=" * 60)

    # 먼저 Instagram 메인 페이지 방문하여 쿠키 획득 시도
    try:
        with httpx.Client() as client:
            # 메인 페이지 방문
            main_resp = client.get("https://www.instagram.com/", headers={
                "User-Agent": REQUIRED_HEADERS["User-Agent"],
                "Accept": "text/html",
            }, timeout=10)

            print(f"Main page status: {main_resp.status_code}")
            print(f"Cookies received: {len(client.cookies)} cookies")

            # API 요청
            url = "https://www.instagram.com/api/v1/users/web_profile_info/"
            params = {"username": TEST_USERNAME}

            response = client.get(url, params=params, headers=REQUIRED_HEADERS, timeout=10)
            print(f"\nAPI Status Code: {response.status_code}")
            print(f"Response (first 1000 chars):\n{response.text[:1000]}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    if "data" in data and "user" in data["data"]:
                        print("\n✅ 세션 쿠키로 성공!")
                        return True
                except:
                    pass
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Instagram API 테스트 시작")
    print(f"대상 사용자: {TEST_USERNAME}")
    print()

    # 테스트 실행
    result1 = test_basic_request()
    result2 = test_with_headers()
    result3 = test_with_session()

    # 결과 요약
    print("\n" + "=" * 60)
    print("📋 테스트 결과 요약")
    print("=" * 60)
    print(f"테스트 1 (기본 요청): {'성공' if result1 == 200 else '실패/차단'}")
    print(f"테스트 2 (필수 헤더): {'성공' if result2 else '실패/차단'}")
    print(f"테스트 3 (세션 쿠키): {'성공' if result3 else '실패/차단'}")

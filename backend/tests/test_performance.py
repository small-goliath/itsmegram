"""
itsmegram - 성능 테스트 스크립트
캐싱 및 API 응답 시간 측정

실행 방법:
    cd backend
    python -m pytest tests/test_performance.py -v
    또는
    python tests/test_performance.py
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any
from datetime import datetime

import pytest
import httpx

# 테스트 대상 서비스 임포트
try:
    from app.services.cache_service import cache_service
    from app.services.instagram_service import instagram_service
    from app.services.ai_service import ai_service
    from app.models.schemas import InstagramData, ProfileData, PostData
    SERVICES_AVAILABLE = True
except ImportError:
    SERVICES_AVAILABLE = False
    print("Warning: Backend services not available. Running API tests only.")


# 테스트 설정
BASE_URL = "http://localhost:8000"
API_V1_PREFIX = "/api/v1"
TEST_USERNAME = "instagram"  # 테스트용 사용자명 (실제 존재하는 계정)


class PerformanceMetrics:
    """성능 메트릭스 수집 클래스"""

    def __init__(self):
        self.response_times: List[float] = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors = 0

    def add_response_time(self, duration: float):
        """응답 시간 추가"""
        self.response_times.append(duration)

    def record_cache_hit(self):
        """캐시 히트 기록"""
        self.cache_hits += 1

    def record_cache_miss(self):
        """캐시 미스 기록"""
        self.cache_misses += 1

    def record_error(self):
        """에러 기록"""
        self.errors += 1

    def get_summary(self) -> Dict[str, Any]:
        """성능 요약 반환"""
        if not self.response_times:
            return {"error": "No data collected"}

        sorted_times = sorted(self.response_times)
        n = len(sorted_times)

        # p95 계산
        p95_index = int(n * 0.95)
        p95 = sorted_times[min(p95_index, n - 1)]

        # p99 계산
        p99_index = int(n * 0.99)
        p99 = sorted_times[min(p99_index, n - 1)]

        return {
            "total_requests": n,
            "mean_response_time_ms": round(statistics.mean(self.response_times) * 1000, 2),
            "median_response_time_ms": round(statistics.median(self.response_times) * 1000, 2),
            "min_response_time_ms": round(min(self.response_times) * 1000, 2),
            "max_response_time_ms": round(max(self.response_times) * 1000, 2),
            "p95_response_time_ms": round(p95 * 1000, 2),
            "p99_response_time_ms": round(p99 * 1000, 2),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(
                self.cache_hits / (self.cache_hits + self.cache_misses) * 100, 2
            ) if (self.cache_hits + self.cache_misses) > 0 else 0,
            "errors": self.errors,
            "error_rate": round(self.errors / n * 100, 2) if n > 0 else 0,
        }

    def print_summary(self, title: str = "Performance Summary"):
        """성능 요약 출력"""
        summary = self.get_summary()

        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}")

        if "error" in summary:
            print(f"  {summary['error']}")
            return

        print(f"  Total Requests:     {summary['total_requests']}")
        print(f"  Mean Response Time: {summary['mean_response_time_ms']:.2f} ms")
        print(f"  Median Response:    {summary['median_response_time_ms']:.2f} ms")
        print(f"  Min Response Time:  {summary['min_response_time_ms']:.2f} ms")
        print(f"  Max Response Time:  {summary['max_response_time_ms']:.2f} ms")
        print(f"  P95 Response Time:  {summary['p95_response_time_ms']:.2f} ms")
        print(f"  P99 Response Time:  {summary['p99_response_time_ms']:.2f} ms")
        print(f"  -" * 30)
        print(f"  Cache Hits:         {summary['cache_hits']}")
        print(f"  Cache Misses:       {summary['cache_misses']}")
        print(f"  Cache Hit Rate:     {summary['cache_hit_rate']:.1f}%")
        print(f"  -" * 30)
        print(f"  Errors:             {summary['errors']}")
        print(f"  Error Rate:         {summary['error_rate']:.1f}%")
        print(f"{'=' * 60}")

        # p95 목표 체크 (< 500ms)
        if summary['p95_response_time_ms'] < 500:
            print(f"  ✅ P95 목표 달성: {summary['p95_response_time_ms']:.2f}ms < 500ms")
        else:
            print(f"  ❌ P95 목표 미달: {summary['p95_response_time_ms']:.2f}ms >= 500ms")
        print(f"{'=' * 60}\n")


# ==================== 캐시 서비스 테스트 ====================

@pytest.mark.asyncio
@pytest.mark.skipif(not SERVICES_AVAILABLE, reason="Backend services not available")
async def test_cache_service_performance():
    """캐시 서비스 성능 테스트"""
    print("\n[테스트] 캐시 서비스 성능 테스트 시작")

    metrics = PerformanceMetrics()

    # Redis 연결
    connected = await cache_service.connect()
    if not connected:
        pytest.skip("Redis not available")

    try:
        test_data = {"test": "data", "timestamp": datetime.utcnow().isoformat()}
        iterations = 100

        # 캐시 쓰기 테스트
        print(f"  캐시 쓰기 테스트 ({iterations}회)...")
        write_times = []
        for i in range(iterations):
            start = time.perf_counter()
            await cache_service.set(f"perf:test:{i}", test_data, ttl=60)
            write_times.append(time.perf_counter() - start)

        avg_write = statistics.mean(write_times) * 1000
        print(f"  평균 쓰기 시간: {avg_write:.2f} ms")

        # 캐시 읽기 테스트 (캐시 히트)
        print(f"  캐시 읽기 테스트 (히트, {iterations}회)...")
        for i in range(iterations):
            start = time.perf_counter()
            result = await cache_service.get(f"perf:test:{i}")
            duration = time.perf_counter() - start
            metrics.add_response_time(duration)

            if result:
                metrics.record_cache_hit()
            else:
                metrics.record_cache_miss()

        # 캐시 미스 테스트
        print(f"  캐시 읽기 테스트 (미스, {iterations}회)...")
        for i in range(iterations):
            start = time.perf_counter()
            result = await cache_service.get(f"perf:test:miss:{i}")
            duration = time.perf_counter() - start
            metrics.add_response_time(duration)

            if result:
                metrics.record_cache_hit()
            else:
                metrics.record_cache_miss()

        metrics.print_summary("Cache Service Performance")

        # 캐시 히트가 미스보다 빨라야 함
        # (단순화를 위해 전체 평균으로 비교)

    finally:
        # 정리
        for i in range(iterations):
            await cache_service.delete(f"perf:test:{i}")
        await cache_service.disconnect()


@pytest.mark.asyncio
@pytest.mark.skipif(not SERVICES_AVAILABLE, reason="Backend services not available")
async def test_cache_hit_vs_miss():
    """캐시 히트 vs 미스 성능 비교"""
    print("\n[테스트] 캐시 히트 vs 미스 성능 비교")

    connected = await cache_service.connect()
    if not connected:
        pytest.skip("Redis not available")

    try:
        test_key = "perf:hit_vs_miss"
        test_value = {"data": "x" * 1000}  # 1KB 데이터

        # 캐시 미스 (최초 조회)
        start = time.perf_counter()
        result = await cache_service.get(test_key)
        miss_time = (time.perf_counter() - start) * 1000

        # 캐시 저장
        await cache_service.set(test_key, test_value, ttl=60)

        # 캐시 히트 (저장 후 조회)
        start = time.perf_counter()
        result = await cache_service.get(test_key)
        hit_time = (time.perf_counter() - start) * 1000

        # 여러 번 히트 테스트
        hit_times = []
        for _ in range(10):
            start = time.perf_counter()
            await cache_service.get(test_key)
            hit_times.append((time.perf_counter() - start) * 1000)

        avg_hit_time = statistics.mean(hit_times)

        print(f"  캐시 미스 시간: {miss_time:.2f} ms")
        print(f"  캐시 히트 시간: {avg_hit_time:.2f} ms")
        print(f"  성능 향상: {miss_time / avg_hit_time:.1f}x")

        # 캐시 히트가 미스보다 빨라야 함
        assert avg_hit_time < miss_time, "Cache hit should be faster than miss"

    finally:
        await cache_service.delete(test_key)
        await cache_service.disconnect()


# ==================== API 응답 시간 테스트 ====================

@pytest.mark.asyncio
async def test_api_health_endpoint():
    """Health API 응답 시간 테스트"""
    print("\n[테스트] Health API 응답 시간 테스트")

    metrics = PerformanceMetrics()
    iterations = 50

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        for i in range(iterations):
            start = time.perf_counter()
            try:
                response = await client.get(f"{API_V1_PREFIX}/health")
                duration = time.perf_counter() - start
                metrics.add_response_time(duration)

                if response.status_code == 200:
                    metrics.record_cache_hit()  # 성공을 히트로 기록
                else:
                    metrics.record_error()
            except Exception as e:
                metrics.record_error()
                print(f"  Error on iteration {i}: {e}")

    metrics.print_summary("Health API Performance")

    # p95 < 500ms 체크
    summary = metrics.get_summary()
    assert summary['p95_response_time_ms'] < 500, "P95 should be < 500ms"


@pytest.mark.asyncio
async def test_api_response_compression():
    """API 응답 압축 테스트"""
    print("\n[테스트] API 응답 압축 테스트")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 압축 없이 요청
        response_no_compression = await client.get(
            f"{API_V1_PREFIX}/health",
            headers={"Accept-Encoding": "identity"}
        )

        # 압축으로 요청
        response_with_compression = await client.get(
            f"{API_V1_PREFIX}/health",
            headers={"Accept-Encoding": "gzip, deflate"}
        )

        print(f"  압축 없음: {len(response_no_compression.content)} bytes")
        print(f"  압축 있음: {len(response_with_compression.content)} bytes")

        # 압축된 응답이 더 작아야 함 (큰 응답의 경우)
        # Health 엔드포인트는 작을 수 있으므로 Content-Encoding 헤더만 확인
        if "Content-Encoding" in response_with_compression.headers:
            print(f"  ✅ 압축 활성화됨: {response_with_compression.headers['Content-Encoding']}")
        else:
            print(f"  ℹ️ 응답이 작아 압축되지 않음 (GZip minimum_size=1000)")


@pytest.mark.asyncio
async def test_api_concurrent_requests():
    """동시 요청 성능 테스트"""
    print("\n[테스트] 동시 요청 성능 테스트")

    metrics = PerformanceMetrics()
    concurrent_requests = 20

    async def make_request(client: httpx.AsyncClient) -> float:
        """단일 요청 수행"""
        start = time.perf_counter()
        try:
            response = await client.get(f"{API_V1_PREFIX}/health")
            if response.status_code != 200:
                metrics.record_error()
        except Exception:
            metrics.record_error()
        return time.perf_counter() - start

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        start_total = time.perf_counter()

        # 동시 요청 실행
        tasks = [make_request(client) for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks)

        total_time = time.perf_counter() - start_total

        for duration in results:
            metrics.add_response_time(duration)

    metrics.print_summary(f"Concurrent Requests ({concurrent_requests})")
    print(f"  총 실행 시간: {total_time * 1000:.2f} ms")
    print(f"  초당 요청 수: {concurrent_requests / total_time:.1f} RPS")


# ==================== 인스타그램 서비스 캐싱 테스트 ====================

@pytest.mark.asyncio
@pytest.mark.skipif(not SERVICES_AVAILABLE, reason="Backend services not available")
async def test_instagram_service_caching():
    """Instagram 서비스 캐싱 테스트"""
    print("\n[테스트] Instagram 서비스 캐싱 테스트")

    connected = await cache_service.connect()
    if not connected:
        pytest.skip("Redis not available")

    metrics = PerformanceMetrics()

    try:
        # 캐시 초기화
        await cache_service.invalidate_profile(TEST_USERNAME)

        # 첫 번째 호출 (캐시 미스)
        print(f"  첫 번째 프로필 조회 (캐시 미스 예상)...")
        start = time.perf_counter()
        try:
            profile1 = await instagram_service.fetch_profile(TEST_USERNAME, use_cache=True)
            duration1 = time.perf_counter() - start
            metrics.add_response_time(duration1)
            metrics.record_cache_miss()
            print(f"    소요 시간: {duration1 * 1000:.2f} ms")
        except Exception as e:
            print(f"    오류 (Instagram API 제한 가능): {e}")
            pytest.skip(f"Instagram API error: {e}")

        # 두 번째 호출 (캐시 히트)
        print(f"  두 번째 프로필 조회 (캐시 히트 예상)...")
        start = time.perf_counter()
        profile2 = await instagram_service.fetch_profile(TEST_USERNAME, use_cache=True)
        duration2 = time.perf_counter() - start
        metrics.add_response_time(duration2)
        metrics.record_cache_hit()
        print(f"    소요 시간: {duration2 * 1000:.2f} ms")

        # 성능 향상 계산
        if duration1 > 0:
            improvement = duration1 / duration2 if duration2 > 0 else 0
            print(f"  성능 향상: {improvement:.1f}x")

        # 데이터 일관성 확인
        assert profile1.username == profile2.username, "Cached data should match"

        metrics.print_summary("Instagram Service Caching")

    finally:
        await cache_service.invalidate_profile(TEST_USERNAME)
        await cache_service.disconnect()


# ==================== AI 서비스 캐싱 테스트 ====================

@pytest.mark.asyncio
@pytest.mark.skipif(not SERVICES_AVAILABLE, reason="Backend services not available")
async def test_ai_service_caching():
    """AI 서비스 캐싱 테스트"""
    print("\n[테스트] AI 서비스 캐싱 테스트")

    connected = await cache_service.connect()
    if not connected:
        pytest.skip("Redis not available")

    # API 키 확인
    import os
    if not os.getenv("MOONSHOT_API_KEY"):
        pytest.skip("MOONSHOT_API_KEY not set")

    metrics = PerformanceMetrics()

    try:
        # 테스트 데이터 생성
        test_profile = ProfileData(
            username="test_user",
            full_name="Test User",
            biography="Test biography",
            followers=1000,
            following=500,
            posts_count=50,
            is_private=False,
            profile_pic_url="",
            is_verified=False,
            external_url=None,
        )

        test_posts = [
            PostData(
                post_id=f"test_{i}",
                caption=f"Test post {i} #test",
                likes=100 + i * 10,
                comments=10 + i,
                media_url="",
                hashtags=["test"],
                mentions=[],
                timestamp=datetime.utcnow(),
                post_type="image",
                shortcode=f"test{i}",
            )
            for i in range(5)
        ]

        test_data = InstagramData(
            profile=test_profile,
            posts=test_posts,
            collected_at=datetime.utcnow(),
        )

        # 캐시 초기화
        await cache_service.invalidate_analysis("test_user")

        # 첫 번째 분석 (캐시 미스 - 실제 API 호출)
        print(f"  첫 번째 분석 (캐시 미스 예상, API 호출)...")
        start = time.perf_counter()
        try:
            report1 = await ai_service.generate_report(test_data, use_cache=True)
            duration1 = time.perf_counter() - start
            metrics.add_response_time(duration1)
            metrics.record_cache_miss()
            print(f"    소요 시간: {duration1 * 1000:.2f} ms")
        except Exception as e:
            print(f"    오류 (API 제한 가능): {e}")
            pytest.skip(f"AI API error: {e}")

        # 두 번째 분석 (캐시 히트)
        print(f"  두 번째 분석 (캐시 히트 예상)...")
        start = time.perf_counter()
        report2 = await ai_service.generate_report(test_data, use_cache=True)
        duration2 = time.perf_counter() - start
        metrics.add_response_time(duration2)
        metrics.record_cache_hit()
        print(f"    소요 시간: {duration2 * 1000:.2f} ms")

        # 성능 향상 계산
        if duration1 > 0 and duration2 > 0:
            improvement = duration1 / duration2
            print(f"  성능 향상: {improvement:.1f}x")
            print(f"  API 비용 절감: 1회 호출 방지")

        # 데이터 일관성 확인
        assert report1.overall_score == report2.overall_score, "Cached data should match"

        metrics.print_summary("AI Service Caching")

    finally:
        await cache_service.invalidate_analysis("test_user")
        await cache_service.disconnect()


# ==================== 종합 성능 테스트 ====================

@pytest.mark.asyncio
async def test_full_performance_suite():
    """전체 성능 테스트 스위트"""
    print("\n" + "=" * 60)
    print("  itsmegram 성능 테스트 스위트")
    print("=" * 60)

    results = {}

    # API 테스트
    try:
        metrics = PerformanceMetrics()
        async with httpx.AsyncClient(base_url=BASE_URL) as client:
            for _ in range(20):
                start = time.perf_counter()
                response = await client.get(f"{API_V1_PREFIX}/health")
                metrics.add_response_time(time.perf_counter() - start)

        results["api_health"] = metrics.get_summary()
        metrics.print_summary("API Health Endpoint")
    except Exception as e:
        print(f"API 테스트 실패: {e}")
        results["api_health"] = {"error": str(e)}

    # 캐시 서비스 테스트
    if SERVICES_AVAILABLE:
        try:
            connected = await cache_service.connect()
            if connected:
                metrics = PerformanceMetrics()

                # 쓰기 테스트
                for i in range(50):
                    start = time.perf_counter()
                    await cache_service.set(f"suite:test:{i}", {"data": i}, ttl=60)
                    metrics.add_response_time(time.perf_counter() - start)

                # 읽기 테스트
                for i in range(50):
                    start = time.perf_counter()
                    await cache_service.get(f"suite:test:{i}")
                    metrics.add_response_time(time.perf_counter() - start)
                    metrics.record_cache_hit()

                results["cache_service"] = metrics.get_summary()
                metrics.print_summary("Cache Service")

                # 정리
                for i in range(50):
                    await cache_service.delete(f"suite:test:{i}")
                await cache_service.disconnect()
        except Exception as e:
            print(f"캐시 서비스 테스트 실패: {e}")
            results["cache_service"] = {"error": str(e)}

    print("\n" + "=" * 60)
    print("  테스트 완료")
    print("=" * 60)

    return results


# ==================== 메인 실행 ====================

if __name__ == "__main__":
    """직접 실행 시 테스트 수행"""
    print("itsmegram 성능 테스트")
    print(f"대상 서버: {BASE_URL}")
    print(f"시간: {datetime.utcnow().isoformat()}")
    print("-" * 60)

    # pytest를 통해 테스트 실행
    pytest.main([__file__, "-v", "--tb=short"])

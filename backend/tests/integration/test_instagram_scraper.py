"""
Integration tests for Instagram scraper v2.0
Tests HTTP-based Instagram data collection
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock

from app.services.instagram_service import InstagramService
from app.utils.exceptions import ProfileNotFoundError, PrivateAccountError, RateLimitError
from app.clients.http_client import InstagramHTTPClient


@pytest.fixture
def instagram_service():
    """Create Instagram service instance for testing"""
    return InstagramService()


@pytest.fixture
def mock_profile_response():
    """Mock Instagram profile API response"""
    return {
        "data": {
            "user": {
                "username": "testuser",
                "full_name": "Test User",
                "biography": "This is a test bio",
                "edge_followed_by": {"count": 1000},
                "edge_follow": {"count": 500},
                "edge_owner_to_timeline_media": {"count": 50},
                "is_private": False,
                "is_verified": True,
                "profile_pic_url_hd": "https://example.com/profile.jpg",
                "external_url": "https://example.com",
            }
        }
    }


@pytest.fixture
def mock_posts_response():
    """Mock Instagram posts API response"""
    return {
        "data": {
            "user": {
                "edge_owner_to_timeline_media": {
                    "edges": [
                        {
                            "node": {
                                "id": "123456789",
                                "shortcode": "ABC123",
                                "edge_media_to_caption": {
                                    "edges": [{"node": {"text": "Test caption #test"}}]
                                },
                                "edge_liked_by": {"count": 100},
                                "edge_media_to_comment": {"count": 10},
                                "display_url": "https://example.com/image.jpg",
                                "taken_at_timestamp": 1704067200,
                                "is_video": False,
                            }
                        }
                    ]
                }
            }
        }
    }


@pytest.mark.asyncio
async def test_fetch_profile_success(instagram_service, mock_profile_response):
    """Test successful profile fetch"""
    with patch.object(
        InstagramHTTPClient, "fetch_profile", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_profile_response

        result = await instagram_service.fetch_profile("testuser", use_cache=False)

        assert result.username == "testuser"
        assert result.full_name == "Test User"
        assert result.biography == "This is a test bio"
        assert result.followers == 1000
        assert result.following == 500
        assert result.posts_count == 50
        assert result.is_private is False
        assert result.is_verified is True
        assert result.profile_pic_url == "https://example.com/profile.jpg"


@pytest.mark.asyncio
async def test_fetch_profile_not_found(instagram_service):
    """Test profile not found error handling"""
    with patch.object(
        InstagramHTTPClient, "fetch_profile", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.side_effect = ProfileNotFoundError("nonexistentuser")

        with pytest.raises(ProfileNotFoundError):
            await instagram_service.fetch_profile("nonexistentuser", use_cache=False)


@pytest.mark.asyncio
async def test_fetch_profile_private_account(instagram_service, mock_profile_response):
    """Test private account error handling"""
    mock_profile_response["data"]["user"]["is_private"] = True

    with patch.object(
        InstagramHTTPClient, "fetch_profile", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_profile_response

        with pytest.raises(PrivateAccountError):
            await instagram_service.fetch_profile("privateuser", use_cache=False)


@pytest.mark.asyncio
async def test_fetch_posts_success(instagram_service, mock_posts_response):
    """Test successful posts fetch"""
    with patch.object(
        InstagramHTTPClient, "fetch_profile", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_posts_response

        result = await instagram_service.fetch_posts("testuser", limit=1, use_cache=False)

        assert len(result) == 1
        assert result[0].post_id == "123456789"
        assert result[0].shortcode == "ABC123"
        assert result[0].caption == "Test caption #test"
        assert result[0].likes == 100
        assert result[0].comments == 10
        assert result[0].post_type == "image"


@pytest.mark.asyncio
async def test_fetch_posts_limit(instagram_service, mock_posts_response):
    """Test posts fetch with limit"""
    # Add more posts to response
    edges = mock_posts_response["data"]["user"]["edge_owner_to_timeline_media"]["edges"]
    for i in range(10):
        edges.append(edges[0].copy())

    with patch.object(
        InstagramHTTPClient, "fetch_profile", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = mock_posts_response

        result = await instagram_service.fetch_posts("testuser", limit=5, use_cache=False)

        assert len(result) == 5


@pytest.mark.asyncio
async def test_fetch_full_data(instagram_service, mock_profile_response, mock_posts_response):
    """Test fetching full data (profile + posts)"""
    # Combine responses
    full_response = mock_profile_response.copy()
    full_response["data"]["user"]["edge_owner_to_timeline_media"] = mock_posts_response["data"]["user"]["edge_owner_to_timeline_media"]

    with patch.object(
        InstagramHTTPClient, "fetch_profile", new_callable=AsyncMock
    ) as mock_fetch:
        mock_fetch.return_value = full_response

        result = await instagram_service.fetch_full_data("testuser", posts_limit=1, use_cache=False)

        assert result.profile.username == "testuser"
        assert len(result.posts) == 1
        assert result.posts[0].post_id == "123456789"


@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting - sequential requests should have delays"""
    from app.services.rate_limiter import AdaptiveRateLimiter

    limiter = AdaptiveRateLimiter(tokens_per_second=5.0, bucket_size=5)

    start_time = time.time()

    # Make 6 requests (should take at least 0.2 seconds due to rate limiting)
    for _ in range(6):
        await limiter.acquire()

    elapsed = time.time() - start_time

    # With 5 tokens/sec, 6 requests should take at least 0.2 seconds
    assert elapsed >= 0.15  # Allow some tolerance


@pytest.mark.asyncio
async def test_rate_limiter_adaptive():
    """Test adaptive rate limiter adjustment"""
    from app.services.rate_limiter import AdaptiveRateLimiter

    limiter = AdaptiveRateLimiter(tokens_per_second=5.0, bucket_size=5)

    # Report 10 successes (should increase rate)
    for _ in range(10):
        limiter.report_success()

    # Rate should have increased
    assert limiter.tokens_per_second > 5.0
    assert limiter.bucket_size > 5

    # Report rate limit hit (should decrease rate)
    limiter.report_rate_limited()

    # Rate should have decreased
    assert limiter.tokens_per_second < 6.0
    assert limiter.bucket_size < 6


@pytest.mark.asyncio
async def test_circuit_breaker():
    """Test circuit breaker pattern"""
    from app.services.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError

    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

    async def success_func():
        return "success"

    async def fail_func():
        raise Exception("Test error")

    # Test successful calls
    result = await breaker.call(success_func)
    assert result == "success"
    assert breaker.state.value == "closed"

    # Test failures - should open circuit after 3 failures
    for _ in range(3):
        try:
            await breaker.call(fail_func)
        except Exception:
            pass

    assert breaker.state.value == "open"

    # Should raise CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError):
        await breaker.call(success_func)


@pytest.mark.asyncio
async def test_queue_manager():
    """Test queue manager functionality"""
    from app.services.queue_manager import QueueManager, QueueStatus

    queue = QueueManager(max_concurrent=2, max_queue_size=5)
    await queue.start()

    results = []

    async def test_task():
        await asyncio.sleep(0.1)
        results.append("done")
        return "completed"

    # Enqueue jobs
    job_ids = []
    for i in range(3):
        job_id = await queue.enqueue(f"user{i}", test_task)
        assert job_id is not None
        job_ids.append(job_id)

    # Wait for jobs to complete
    await asyncio.sleep(0.5)

    # Check results
    assert len(results) == 3

    # Check status
    for job_id in job_ids:
        status = queue.get_status(job_id)
        assert status is not None
        assert status["status"] == QueueStatus.COMPLETED

    await queue.stop()


@pytest.mark.asyncio
async def test_queue_manager_full():
    """Test queue manager when full"""
    from app.services.queue_manager import QueueManager

    queue = QueueManager(max_concurrent=1, max_queue_size=2)

    async def slow_task():
        await asyncio.sleep(10)  # Long running task
        return "done"

    # Fill up the queue
    await queue.start()

    # Queue can hold 2 items, but we're not consuming them
    job1 = await queue.enqueue("user1", slow_task)
    job2 = await queue.enqueue("user2", slow_task)
    job3 = await queue.enqueue("user3", slow_task)

    # Third job should be rejected
    assert job1 is not None
    assert job2 is not None
    assert job3 is None  # Queue full

    await queue.stop()

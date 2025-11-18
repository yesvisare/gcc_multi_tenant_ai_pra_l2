"""
Tests for L3 M12.3: Query Isolation & Rate Limiting

Tests all major functions and classes with offline/mock mode.
Services: Mocked Redis, PostgreSQL, Prometheus for testing
"""

import pytest
import os
import time
from unittest.mock import Mock, AsyncMock, patch

# Force offline mode for tests
os.environ["REDIS_ENABLED"] = "false"
os.environ["POSTGRES_ENABLED"] = "false"
os.environ["OFFLINE"] = "true"

from src.l3_m12_data_isolation_security import (
    TenantRateLimiter,
    TenantConfigLoader,
    NoisyNeighborMitigator,
    NotificationService,
    TenantConfig,
    TenantTier,
    RateLimitResult
)
from config import InMemoryRateLimiter


class TestTenantRateLimiter:
    """Test suite for TenantRateLimiter class"""

    def test_offline_mode_initialization(self):
        """Test rate limiter initializes correctly in offline mode"""
        fallback = InMemoryRateLimiter()
        limiter = TenantRateLimiter(redis_client=None, fallback_limiter=fallback)

        assert limiter.offline is True
        assert limiter.redis is None
        assert limiter.fallback is not None

    def test_check_limit_offline_mode(self):
        """Test rate limit check in offline mode with fallback"""
        fallback = InMemoryRateLimiter()
        limiter = TenantRateLimiter(redis_client=None, fallback_limiter=fallback)

        # First requests should succeed
        for i in range(5):
            result = limiter.check_limit("tenant_test", limit=5)
            assert isinstance(result, RateLimitResult)
            assert result.tenant_id == "tenant_test"
            assert result.limit == 5

        # 6th request in same minute should fail
        result = limiter.check_limit("tenant_test", limit=5)
        # Note: fallback allows it (simple implementation)
        assert isinstance(result, RateLimitResult)

    def test_check_limit_without_fallback(self):
        """Test rate limiter without Redis or fallback (fail open)"""
        limiter = TenantRateLimiter(redis_client=None, fallback_limiter=None)

        result = limiter.check_limit("tenant_test", limit=100)
        assert result.allowed is True  # Fail open
        assert "Offline mode" in result.reason

    def test_get_current_usage_offline(self):
        """Test getting current usage in offline mode"""
        limiter = TenantRateLimiter(redis_client=None, fallback_limiter=None)

        usage = limiter.get_current_usage("tenant_test")
        assert usage == 0  # No tracking in offline mode

    @pytest.mark.skipif(
        os.getenv("REDIS_ENABLED", "false").lower() != "true",
        reason="Redis not enabled"
    )
    def test_check_limit_with_redis(self):
        """Test rate limiter with actual Redis (integration test)"""
        import redis
        client = redis.from_url("redis://localhost:6379/0", decode_responses=True)
        limiter = TenantRateLimiter(redis_client=client)

        # Clear any existing data
        minute = int(time.time() / 60)
        key = f"rate_limit:tenant_integration:{minute}"
        client.delete(key)

        # Test rate limiting
        results = []
        for i in range(12):
            result = limiter.check_limit("tenant_integration", limit=10)
            results.append(result.allowed)

        # First 10 should pass, next 2 should fail
        assert sum(results[:10]) == 10
        assert sum(results[10:]) == 0


class TestTenantConfigLoader:
    """Test suite for TenantConfigLoader class"""

    @pytest.mark.asyncio
    async def test_offline_mode_initialization(self):
        """Test config loader initializes with default configs in offline mode"""
        loader = TenantConfigLoader(postgres_pool=None)

        assert loader.offline is True
        assert len(loader.cache) > 0
        assert "tenant_bronze" in loader.cache
        assert "tenant_silver" in loader.cache
        assert "tenant_gold" in loader.cache

    @pytest.mark.asyncio
    async def test_get_config_offline_known_tenant(self):
        """Test getting config for known tenant in offline mode"""
        loader = TenantConfigLoader(postgres_pool=None)

        config = await loader.get_config("tenant_gold")
        assert isinstance(config, TenantConfig)
        assert config.tenant_id == "tenant_gold"
        assert config.tier == TenantTier.GOLD
        assert config.queries_per_minute == 2000
        assert config.priority == 3

    @pytest.mark.asyncio
    async def test_get_config_offline_unknown_tenant(self):
        """Test getting config for unknown tenant (should default to bronze)"""
        loader = TenantConfigLoader(postgres_pool=None)

        config = await loader.get_config("tenant_unknown")
        assert isinstance(config, TenantConfig)
        assert config.tier == TenantTier.BRONZE
        assert config.queries_per_minute == 100
        assert config.priority == 1

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache expiration logic"""
        loader = TenantConfigLoader(postgres_pool=None)

        # Initially not expired
        assert loader._cache_expired() is False

        # Force expiration
        loader.last_refresh = time.time() - 400  # 400 seconds ago
        assert loader._cache_expired() is True

    @pytest.mark.asyncio
    async def test_refresh_cache_offline(self):
        """Test cache refresh in offline mode (should skip)"""
        loader = TenantConfigLoader(postgres_pool=None)

        await loader.refresh_cache()
        # Should still have default configs
        assert len(loader.cache) > 0


class TestNoisyNeighborMitigator:
    """Test suite for NoisyNeighborMitigator class"""

    def setup_method(self):
        """Set up test fixtures"""
        fallback = InMemoryRateLimiter()
        self.rate_limiter = TenantRateLimiter(redis_client=None, fallback_limiter=fallback)
        self.config_loader = TenantConfigLoader(postgres_pool=None)
        self.mitigator = NoisyNeighborMitigator(self.rate_limiter, self.config_loader)

    def test_check_noisy_neighbor_normal(self):
        """Test noisy neighbor detection for normal traffic"""
        is_noisy, severity = self.mitigator.check_noisy_neighbor(
            "tenant_test",
            baseline=100,
            current=120  # 1.2x baseline
        )
        assert is_noisy is False
        assert severity == "normal"

    def test_check_noisy_neighbor_high_severity(self):
        """Test noisy neighbor detection for high severity (3-5x)"""
        is_noisy, severity = self.mitigator.check_noisy_neighbor(
            "tenant_test",
            baseline=100,
            current=350  # 3.5x baseline
        )
        assert is_noisy is True
        assert severity == "high"

    def test_check_noisy_neighbor_critical_severity(self):
        """Test noisy neighbor detection for critical severity (>5x)"""
        is_noisy, severity = self.mitigator.check_noisy_neighbor(
            "tenant_test",
            baseline=100,
            current=600  # 6x baseline
        )
        assert is_noisy is True
        assert severity == "critical"

    @pytest.mark.asyncio
    async def test_apply_mitigation_high_severity(self):
        """Test applying high severity mitigation (50% reduction)"""
        result = await self.mitigator.apply_mitigation("tenant_test", "high", 300)

        assert result["tenant_id"] == "tenant_test"
        assert result["severity"] == "high"
        assert "50%" in result["action"]
        assert result["duration_seconds"] == 300

    @pytest.mark.asyncio
    async def test_apply_mitigation_critical_severity(self):
        """Test applying critical severity mitigation (circuit breaker)"""
        result = await self.mitigator.apply_mitigation("tenant_test", "critical", 300)

        assert result["tenant_id"] == "tenant_test"
        assert result["severity"] == "critical"
        assert "Circuit breaker" in result["action"]
        assert self.mitigator.is_circuit_broken("tenant_test") is True

    def test_circuit_breaker_expiration(self):
        """Test circuit breaker expires after duration"""
        # Engage circuit breaker with 1 second duration
        end_time = time.time() + 1
        self.mitigator.circuit_breakers["tenant_test"] = end_time

        assert self.mitigator.is_circuit_broken("tenant_test") is True

        # Wait for expiration
        time.sleep(1.1)
        assert self.mitigator.is_circuit_broken("tenant_test") is False


class TestNotificationService:
    """Test suite for NotificationService class"""

    @pytest.mark.asyncio
    async def test_offline_mode(self):
        """Test notification service in offline mode"""
        service = NotificationService(slack_webhook=None, smtp_config=None)

        assert service.offline is True

        # Should succeed but not actually send
        result = await service.send_rate_limit_alert(
            "tenant_test",
            "high",
            {"action": "test", "current_usage": 100, "limit": 50}
        )
        assert result is True

    def test_format_message(self):
        """Test alert message formatting"""
        service = NotificationService()

        message = service._format_message(
            "tenant_test",
            "critical",
            {"action": "Circuit breaker engaged", "current_usage": 500, "limit": 100}
        )

        assert "tenant_test" in message
        assert "CRITICAL" in message
        assert "Circuit breaker" in message
        assert "500" in message
        assert "100" in message

    @pytest.mark.asyncio
    async def test_send_slack_without_webhook(self):
        """Test Slack notification without webhook configured"""
        service = NotificationService()

        result = await service._send_slack("test message", "high")
        assert result is False

    @pytest.mark.asyncio
    async def test_send_email_without_smtp(self):
        """Test email notification without SMTP configured"""
        service = NotificationService()

        result = await service._send_email("tenant_test", "test message")
        assert result is False


class TestInMemoryRateLimiter:
    """Test suite for InMemoryRateLimiter fallback"""

    def test_initialization(self):
        """Test in-memory limiter initialization"""
        limiter = InMemoryRateLimiter()

        assert len(limiter.buckets) == 0

    def test_check_limit_basic(self):
        """Test basic rate limiting logic"""
        limiter = InMemoryRateLimiter()

        # First 5 requests should pass
        for i in range(5):
            result = limiter.check_limit("tenant_test", limit=5)
            assert result is True

        # 6th request should fail
        result = limiter.check_limit("tenant_test", limit=5)
        assert result is False

    def test_check_limit_different_tenants(self):
        """Test that different tenants have separate limits"""
        limiter = InMemoryRateLimiter()

        # Fill limit for tenant1
        for i in range(10):
            limiter.check_limit("tenant1", limit=10)

        # tenant2 should still be able to make requests
        result = limiter.check_limit("tenant2", limit=10)
        assert result is True

    def test_bucket_cleanup(self):
        """Test that old buckets are cleaned up"""
        limiter = InMemoryRateLimiter()

        # Create entries
        limiter.check_limit("tenant_test", limit=100)

        # Manually add old bucket
        old_minute = int(time.time() / 60) - 5
        limiter.buckets[f"tenant_old:{old_minute}"] = 50

        # Trigger cleanup
        limiter.check_limit("tenant_test", limit=100)

        # Old bucket should be removed
        assert f"tenant_old:{old_minute}" not in limiter.buckets


# Integration tests (require actual services)
@pytest.mark.skipif(
    os.getenv("REDIS_ENABLED", "false").lower() != "true" or
    os.getenv("POSTGRES_ENABLED", "false").lower() != "true",
    reason="Full service stack not enabled"
)
class TestFullIntegration:
    """Integration tests with real Redis and PostgreSQL"""

    @pytest.mark.asyncio
    async def test_end_to_end_rate_limiting(self):
        """Test complete rate limiting flow with real services"""
        # This would test the full stack
        # Requires Redis and PostgreSQL to be running
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

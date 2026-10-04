"""
Automated unit verification test for DNS Resolver, Cache, and Statistics.
"""
import time
from dns_cache import DNSCache
from dns_resolver import DNSResolverService
from statistics import StatsManager

def run_tests():
    print("=== Starting Core Verification Tests ===")
    cache = DNSCache()
    resolver = DNSResolverService(cache=cache)
    stats = StatsManager()

    # Test 1: First query -> Cache Miss
    r1 = resolver.resolve("google.com", "A")
    stats.record_query(r1)
    assert not r1.is_cache_hit, "First query should be CACHE MISS"
    assert r1.status == "SUCCESS", f"Query status should be SUCCESS, got {r1.status}"
    assert len(r1.records) > 0, "Should return at least 1 record"
    print(f"Test 1 Passed: First query -> CACHE MISS (Time: {r1.response_time_ms:.2f}ms, Records: {r1.records[:2]})")

    # Test 2: Second query -> Cache Hit
    r2 = resolver.resolve("google.com", "A")
    stats.record_query(r2)
    assert r2.is_cache_hit, "Second query should be CACHE HIT"
    assert r2.response_time_ms < 5.0, f"Cache hit response time should be ultra low, got {r2.response_time_ms}"
    print(f"Test 2 Passed: Second query -> CACHE HIT (Time: {r2.response_time_ms:.2f}ms, Remaining TTL: {r2.remaining_ttl}s)")

    # Test 3: Statistics metrics
    s = stats.get_summary()
    assert s["total_queries"] == 2
    assert s["cache_hits"] == 1
    assert s["cache_misses"] == 1
    assert s["hit_ratio"] == 50.0
    print(f"Test 3 Passed: Statistics -> Hits={s['cache_hits']}, Misses={s['cache_misses']}, Ratio={s['hit_ratio']}%")

    # Test 4: Demo TTL expiration
    r3 = resolver.resolve("example.com", "A", demo_ttl=1)
    stats.record_query(r3)
    assert not r3.is_cache_hit
    assert r3.effective_ttl == 1
    print(f"Test 4a Passed: Initial example.com cached with 1s demo TTL")

    # Immediate query -> should hit
    r3_immediate = resolver.resolve("example.com", "A")
    assert r3_immediate.is_cache_hit
    print(f"Test 4b Passed: Immediate re-query was CACHE HIT")

    # Wait 1.3 seconds for expiration
    print("Waiting 1.3 seconds for TTL to expire...")
    time.sleep(1.3)
    r4 = resolver.resolve("example.com", "A")
    stats.record_query(r4)
    assert not r4.is_cache_hit, "Expired entry MUST result in CACHE MISS and fresh lookup"
    print(f"Test 4c Passed: After TTL expiry -> CACHE MISS (Fresh lookup executed!)")

    # Test 5: Invalid domain
    r5 = resolver.resolve("this-domain-does-not-exist-xyz-987654321.org", "A")
    assert r5.status == "NXDOMAIN", f"Expected NXDOMAIN, got {r5.status}"
    print(f"Test 5 Passed: NXDOMAIN handled properly ({r5.error_message})")

    # Test 6: Purge expired and cache methods
    cache.purge_expired()
    active_count = cache.get_active_count()
    print(f"Test 6 Passed: Cache active count = {active_count}")

    print("\n>>> ALL CORE TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_tests()

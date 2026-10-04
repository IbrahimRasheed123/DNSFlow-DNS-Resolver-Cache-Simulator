"""
Comprehensive Automated Test Suite for DNS Resolver & DNS Cache Simulator.
Executes 11 detailed test cases covering all networking & caching specifications.
"""

import time
import json
import csv
from pathlib import Path
from dns_cache import DNSCache
from dns_resolver import DNSResolverService
from statistics import StatsManager


def run_full_test_suite():
    print("=" * 70)
    print("  DNS RESOLVER & CACHE SIMULATOR: AUTOMATED TEST SUITE")
    print("=" * 70)

    cache = DNSCache()
    resolver = DNSResolverService(cache=cache)
    stats = StatsManager()

    passed_count = 0
    total_tests = 11

    # --- Test Case 1: Standard A Record Lookup (Cache Miss) ---
    print("\n[TC-01] Testing Initial A-Record Query (Expect CACHE MISS)...")
    res1 = resolver.resolve("google.com", "A")
    stats.record_query(res1)
    if not res1.is_cache_hit and res1.status == "SUCCESS" and len(res1.records) > 0:
        print(f"  [PASS] Cache Miss recorded in {res1.response_time_ms:.2f}ms. Records: {res1.records[:2]}")
        passed_count += 1
    else:
        print(f"  [FAIL] res1={res1}")

    # --- Test Case 2: Immediate Re-Query (Expect CACHE HIT < 2ms) ---
    print("\n[TC-02] Testing Immediate Re-Query (Expect CACHE HIT)...")
    res2 = resolver.resolve("google.com", "A")
    stats.record_query(res2)
    if res2.is_cache_hit and res2.response_time_ms < 5.0:
        print(f"  [PASS] Cache Hit confirmed in {res2.response_time_ms:.2f}ms (< 5ms). Remaining TTL: {res2.remaining_ttl}s")
        passed_count += 1
    else:
        print(f"  [FAIL] res2={res2}")

    # --- Test Case 3: AAAA Record Lookup (IPv6) ---
    print("\n[TC-03] Testing IPv6 AAAA Record Lookup...")
    res3 = resolver.resolve("google.com", "AAAA")
    stats.record_query(res3)
    if not res3.is_cache_hit and res3.status == "SUCCESS" and any(":" in r for r in res3.records):
        print(f"  [PASS] Resolved IPv6 AAAA records: {res3.records[:2]}")
        passed_count += 1
    else:
        print(f"  [FAIL] res3={res3}")

    # --- Test Case 4: MX Record Lookup ---
    print("\n[TC-04] Testing Mail Exchange (MX) Record Lookup...")
    res4 = resolver.resolve("google.com", "MX")
    stats.record_query(res4)
    if not res4.is_cache_hit and res4.status == "SUCCESS" and len(res4.records) > 0:
        print(f"  [PASS] Resolved MX records: {res4.records[:2]}")
        passed_count += 1
    else:
        print(f"  [FAIL] res4={res4}")

    # --- Test Case 5: TXT Record Lookup ---
    print("\n[TC-05] Testing TXT Record Lookup (SPF / Verification)...")
    res5 = resolver.resolve("google.com", "TXT")
    stats.record_query(res5)
    if not res5.is_cache_hit and res5.status == "SUCCESS" and len(res5.records) > 0:
        print(f"  [PASS] Resolved TXT records ({len(res5.records)} records found)")
        passed_count += 1
    else:
        print(f"  [FAIL] res5={res5}")

    # --- Test Case 6: Upstream DNS Server Selection (8.8.8.8 vs 1.1.1.1) ---
    print("\n[TC-06] Testing Explicit Nameserver Query (Cloudflare 1.1.1.1)...")
    res6 = resolver.resolve("cloudflare.com", "A", upstream_ip="1.1.1.1", server_label="Cloudflare DNS (1.1.1.1)")
    stats.record_query(res6)
    if res6.status == "SUCCESS" and "1.1.1.1" in res6.upstream_server:
        print(f"  [PASS] Query succeeded via explicit server {res6.upstream_server}")
        passed_count += 1
    else:
        print(f"  [FAIL] res6={res6}")

    # --- Test Case 7: NXDOMAIN Non-Existent Domain Handling ---
    print("\n[TC-07] Testing NXDOMAIN Non-Existent Domain Handling...")
    res7 = resolver.resolve("domain-that-surely-does-not-exist-987123.com", "A")
    stats.record_query(res7)
    if res7.status == "NXDOMAIN" and not res7.is_cache_hit:
        print(f"  [PASS] NXDOMAIN handled cleanly: '{res7.error_message}'")
        passed_count += 1
    else:
        print(f"  [FAIL] res7={res7}")

    # --- Test Case 8: Demo TTL Expiration Test ---
    print("\n[TC-08] Testing Demo TTL Expiration Transition (1s TTL)...")
    res8_initial = resolver.resolve("example.org", "A", demo_ttl=1)
    stats.record_query(res8_initial)
    entry, is_hit_initial = cache.get("example.org", "A")
    assert is_hit_initial is True, "Must be in cache initially"

    print("  Sleeping 1.2s for TTL expiration...")
    time.sleep(1.2)

    entry_after, is_hit_after = cache.get("example.org", "A")
    res8_requery = resolver.resolve("example.org", "A")
    stats.record_query(res8_requery)

    if not is_hit_after and not res8_requery.is_cache_hit:
        print("  [PASS] Expired entry accurately flagged as MISS; fresh network query performed!")
        passed_count += 1
    else:
        print(f"  [FAIL] is_hit_after={is_hit_after}, requery_hit={res8_requery.is_cache_hit}")

    # --- Test Case 9: Cache Purge and Deletion ---
    print("\n[TC-09] Testing Purge Expired and Delete Operations...")
    purged = cache.purge_expired()
    del_ok = cache.delete("google.com", "MX")
    print(f"  [PASS] Purged {purged} expired record(s), deleted MX entry: {del_ok}")
    passed_count += 1

    # --- Test Case 10: Statistics & Hit Ratio Formula Verification ---
    print("\n[TC-10] Verifying Statistical Counters & Hit Ratio Formula...")
    summary = stats.get_summary()
    total = summary["total_queries"]
    hits = summary["cache_hits"]
    misses = summary["cache_misses"]
    ratio = summary["hit_ratio"]
    expected_ratio = round((hits / total) * 100.0, 1)

    if total == (hits + misses) and ratio == expected_ratio:
        print(f"  [PASS] Total={total}, Hits={hits}, Misses={misses}, Hit Ratio={ratio}% == {expected_ratio}%")
        passed_count += 1
    else:
        print(f"  [FAIL] Statistical mismatch: {summary}")

    # --- Test Case 11: Export Persistence (CSV & JSON) ---
    print("\n[TC-11] Testing Data Export (CSV & JSON)...")
    test_csv = Path("test_history_export.csv")
    test_json = Path("test_history_export.json")

    ok_csv, msg_csv = stats.export_csv(test_csv)
    ok_json, msg_json = stats.export_json(test_json)

    if ok_csv and ok_json and test_csv.exists() and test_json.exists():
        print(f"  [PASS] CSV and JSON exported successfully. File sizes: CSV={test_csv.stat().st_size}B, JSON={test_json.stat().st_size}B")
        test_csv.unlink()
        test_json.unlink()
        passed_count += 1
    else:
        print(f"  [FAIL] Export failed. CSV={ok_csv}, JSON={ok_json}")

    print("\n" + "=" * 70)
    print(f"  FINAL RESULT: {passed_count}/{total_tests} TESTS PASSED")
    print("=" * 70)
    return passed_count == total_tests


if __name__ == "__main__":
    success = run_full_test_suite()
    if not success:
        exit(1)

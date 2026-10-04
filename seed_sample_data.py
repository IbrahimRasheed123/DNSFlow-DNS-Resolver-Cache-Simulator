"""
Helper script to populate sample data exports for demonstration.
"""
from dns_cache import DNSCache
from dns_resolver import DNSResolverService
from statistics import StatsManager
from config import HISTORY_EXPORT_CSV, HISTORY_EXPORT_JSON, CACHE_EXPORT_JSON

def seed_data():
    cache = DNSCache()
    resolver = DNSResolverService(cache=cache)
    stats = StatsManager()

    sample_queries = [
        ("google.com", "A"),
        ("google.com", "A"),       # Hit
        ("github.com", "A"),
        ("github.com", "A"),       # Hit
        ("cloudflare.com", "AAAA"),
        ("wikipedia.org", "MX"),
        ("google.com", "MX"),
        ("google.com", "MX"),       # Hit
    ]

    for domain, rtype in sample_queries:
        res = resolver.resolve(domain, rtype)
        stats.record_query(res)

    stats.export_csv(HISTORY_EXPORT_CSV)
    stats.export_json(HISTORY_EXPORT_JSON)
    cache.export_to_json(CACHE_EXPORT_JSON)
    print(f"Sample data generated: {len(stats.history)} queries exported to data/")

if __name__ == "__main__":
    seed_data()

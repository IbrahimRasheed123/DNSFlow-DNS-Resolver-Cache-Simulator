"""
Thread-Safe DNS Cache module with TTL Management and Hit/Miss detection.
Stores resolved records indexed by (domain, record_type).
"""

import threading
import time
import json
from pathlib import Path
from typing import Dict, Tuple, List, Optional
from models import CacheEntry


class DNSCache:
    """
    Local in-memory DNS Cache implementing:
    - Domain + Record Type unique composite keys
    - Authoritative vs Demo TTL tracking
    - Real-time countdown and automatic expiration
    - Thread-safe access with RLock
    """

    def __init__(self):
        self._lock = threading.RLock()
        # Key: (normalized_domain, record_type)
        self._cache: Dict[Tuple[str, str], CacheEntry] = {}

    @staticmethod
    def normalize_domain(domain: str) -> str:
        """Strip protocols, slashes, whitespace and trailing dots."""
        d = domain.strip().lower()
        if d.startswith("http://"):
            d = d[7:]
        elif d.startswith("https://"):
            d = d[8:]
        d = d.split("/")[0].split(":")[0]  # remove path and port if present
        return d.rstrip(".")

    def _make_key(self, domain: str, record_type: str) -> Tuple[str, str]:
        return self.normalize_domain(domain), record_type.strip().upper()

    def get(self, domain: str, record_type: str) -> Tuple[Optional[CacheEntry], bool]:
        """
        Lookup record in cache.
        Returns:
            (entry, is_hit)
            - If not present: (None, False) -> Cache Miss
            - If present but expired: (entry, False) -> Cache Miss (TTL Expired)
            - If present and valid: (entry, True) -> Cache Hit
        """
        key = self._make_key(domain, record_type)
        with self._lock:
            if key not in self._cache:
                return None, False

            entry = self._cache[key]
            if entry.is_expired():
                # Entry exists in cache history, but its TTL has expired!
                return entry, False
            return entry, True

    def put(
        self,
        domain: str,
        record_type: str,
        records: List[str],
        original_ttl: int,
        upstream_server: str,
        demo_ttl: Optional[int] = None,
    ) -> CacheEntry:
        """
        Store or update a resolved DNS record in cache.
        Applies demo TTL if specified (>0), otherwise authoritative TTL.
        """
        norm_domain = self.normalize_domain(domain)
        rec_type = record_type.strip().upper()
        key = (norm_domain, rec_type)

        # Determine effective TTL
        if demo_ttl and demo_ttl > 0:
            effective_ttl = demo_ttl
        else:
            effective_ttl = max(5, int(original_ttl))

        now = time.time()
        entry = CacheEntry(
            domain=norm_domain,
            record_type=rec_type,
            records=records,
            original_ttl=original_ttl,
            configured_ttl=effective_ttl,
            created_at=now,
            expires_at=now + effective_ttl,
            upstream_server=upstream_server,
        )

        with self._lock:
            self._cache[key] = entry

        return entry

    def delete(self, domain: str, record_type: str) -> bool:
        """Delete a specific cache record."""
        key = self._make_key(domain, record_type)
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> int:
        """Clear all entries from cache. Returns count of removed items."""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            return count

    def purge_expired(self) -> int:
        """Remove all entries whose TTL has expired. Returns count purged."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items() if entry.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)

    def get_all(self, include_expired: bool = True) -> List[CacheEntry]:
        """
        Return list of all cached entries.
        Active entries sorted by remaining TTL (lowest first), followed by expired entries.
        """
        with self._lock:
            entries = list(self._cache.values())

        active = [e for e in entries if not e.is_expired()]
        expired = [e for e in entries if e.is_expired()]

        # Sort active by remaining TTL ascending
        active.sort(key=lambda e: e.remaining_ttl())
        # Sort expired by expiry time descending (most recently expired first)
        expired.sort(key=lambda e: e.expires_at, reverse=True)

        if include_expired:
            return active + expired
        return active

    def get_active_count(self) -> int:
        """Count currently valid non-expired cache records."""
        with self._lock:
            return sum(1 for e in self._cache.values() if not e.is_expired())

    def get_expired_count(self) -> int:
        """Count expired records currently lingering in cache."""
        with self._lock:
            return sum(1 for e in self._cache.values() if e.is_expired())

    def get_total_count(self) -> int:
        """Total records in cache."""
        with self._lock:
            return len(self._cache)

    def export_to_json(self, filepath: Path) -> bool:
        """Export current cache state to JSON."""
        try:
            with self._lock:
                data = [e.to_dict() for e in self._cache.values()]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False

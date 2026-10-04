"""
Data models and structure definitions for DNS Resolver & Cache Simulator.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import time


@dataclass
class CacheEntry:
    """Represents a cached DNS record entry with TTL tracking."""
    domain: str
    record_type: str
    records: List[str]
    original_ttl: int               # TTL reported by authoritative DNS server
    configured_ttl: int             # Effective TTL applied (can be demo TTL)
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    upstream_server: str = "System Default"

    def __post_init__(self):
        if self.expires_at == 0.0:
            self.expires_at = self.created_at + max(1, self.configured_ttl)

    def is_expired(self) -> bool:
        """Check if the cache entry has exceeded its TTL lifetime."""
        return time.time() >= self.expires_at

    def remaining_ttl(self) -> int:
        """Return remaining TTL seconds until expiration, min 0."""
        return max(0, int(self.expires_at - time.time()))

    @property
    def status_label(self) -> str:
        """Return human-readable cache status badge text."""
        return "EXPIRED" if self.is_expired() else "ACTIVE"

    def created_at_formatted(self) -> str:
        """Format timestamp as HH:MM:SS."""
        dt = datetime.fromtimestamp(self.created_at)
        return dt.strftime("%H:%M:%S")

    def expires_at_formatted(self) -> str:
        """Format expiry timestamp as HH:MM:SS."""
        dt = datetime.fromtimestamp(self.expires_at)
        return dt.strftime("%H:%M:%S")

    def records_summary(self, max_items: int = 3) -> str:
        """Summarize records for table display."""
        if not self.records:
            return "No records"
        if len(self.records) <= max_items:
            return ", ".join(self.records)
        return f"{', '.join(self.records[:max_items])} (+{len(self.records) - max_items} more)"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize cache entry to dictionary for exports and inspection."""
        return {
            "domain": self.domain,
            "record_type": self.record_type,
            "records": self.records,
            "original_ttl": self.original_ttl,
            "configured_ttl": self.configured_ttl,
            "remaining_ttl": self.remaining_ttl(),
            "status": self.status_label,
            "created_at": self.created_at_formatted(),
            "expires_at": self.expires_at_formatted(),
            "upstream_server": self.upstream_server,
        }


@dataclass
class DNSQueryResult:
    """Represents the complete result of a DNS lookup operation."""
    domain: str
    record_type: str
    records: List[str] = field(default_factory=list)
    original_ttl: int = 0
    effective_ttl: int = 0
    remaining_ttl: int = 0
    response_time_ms: float = 0.0
    is_cache_hit: bool = False
    upstream_server: str = "System Default"
    status: str = "SUCCESS"  # SUCCESS, NXDOMAIN, NO_ANSWER, TIMEOUT, ERROR
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    resolution_path: List[str] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        return self.status == "SUCCESS"

    def formatted_time(self) -> str:
        """Return query execution timestamp formatted as HH:MM:SS."""
        return datetime.fromtimestamp(self.timestamp).strftime("%H:%M:%S")

    def formatted_datetime(self) -> str:
        """Return full timestamp string."""
        return datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> Dict[str, Any]:
        """Convert query result to dictionary."""
        return {
            "timestamp": self.formatted_datetime(),
            "domain": self.domain,
            "record_type": self.record_type,
            "is_cache_hit": self.is_cache_hit,
            "status": self.status,
            "response_time_ms": round(self.response_time_ms, 2),
            "records": self.records,
            "original_ttl": self.original_ttl,
            "remaining_ttl": self.remaining_ttl,
            "upstream_server": self.upstream_server,
            "error_message": self.error_message,
        }


@dataclass
class QueryHistoryItem:
    """Representation of an individual query history entry."""
    index: int
    timestamp_str: str
    domain: str
    record_type: str
    is_cache_hit: bool
    response_time_ms: float
    status: str
    server: str
    records_preview: str
    ttl: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp_str,
            "domain": self.domain,
            "record_type": self.record_type,
            "hit_status": "HIT" if self.is_cache_hit else "MISS",
            "response_time_ms": round(self.response_time_ms, 2),
            "status": self.status,
            "server": self.server,
            "records": self.records_preview,
            "ttl": self.ttl,
        }

"""
Statistics and Query History Tracker for DNS Resolver & Cache Simulator.
Tracks hit/miss ratios, response times, and history logs with CSV/JSON export.
"""

import csv
import json
import threading
from pathlib import Path
from typing import List, Dict, Any, Tuple
from models import DNSQueryResult, QueryHistoryItem


class StatsManager:
    """
    Thread-safe statistics collector and query history tracker.
    Computes real-time networking metrics:
    - Cache Hit Ratio = (Hits / Total) * 100
    - Average response latency
    - Latency distribution for Cache Hits vs Cache Misses
    """

    def __init__(self):
        self._lock = threading.RLock()
        self.total_queries: int = 0
        self.cache_hits: int = 0
        self.cache_misses: int = 0
        self.all_latencies: List[float] = []
        self.hit_latencies: List[float] = []
        self.miss_latencies: List[float] = []
        self.history: List[QueryHistoryItem] = []
        self._next_history_id: int = 1

    def record_query(self, result: DNSQueryResult) -> QueryHistoryItem:
        """Record a completed DNS lookup in statistics and history."""
        with self._lock:
            self.total_queries += 1
            if result.is_cache_hit:
                self.cache_hits += 1
                self.hit_latencies.append(result.response_time_ms)
            else:
                self.cache_misses += 1
                self.miss_latencies.append(result.response_time_ms)

            self.all_latencies.append(result.response_time_ms)

            # Summarize records preview for history
            if result.records:
                records_preview = ", ".join(result.records[:2])
                if len(result.records) > 2:
                    records_preview += f" (+{len(result.records) - 2} more)"
            elif result.error_message:
                records_preview = f"Error: {result.error_message}"
            else:
                records_preview = "No records returned"

            history_item = QueryHistoryItem(
                index=self._next_history_id,
                timestamp_str=result.formatted_time(),
                domain=result.domain,
                record_type=result.record_type,
                is_cache_hit=result.is_cache_hit,
                response_time_ms=result.response_time_ms,
                status=result.status,
                server=result.upstream_server,
                records_preview=records_preview,
                ttl=result.remaining_ttl if result.is_cache_hit else result.effective_ttl,
            )
            self._next_history_id += 1
            self.history.append(history_item)

            return history_item

    def get_summary(self) -> Dict[str, Any]:
        """Compute aggregated statistical metrics."""
        with self._lock:
            total = self.total_queries
            hits = self.cache_hits
            misses = self.cache_misses
            ratio = (hits / total * 100.0) if total > 0 else 0.0

            avg_all = (sum(self.all_latencies) / len(self.all_latencies)) if self.all_latencies else 0.0
            avg_hit = (sum(self.hit_latencies) / len(self.hit_latencies)) if self.hit_latencies else 0.0
            avg_miss = (sum(self.miss_latencies) / len(self.miss_latencies)) if self.miss_latencies else 0.0
            min_latency = min(self.all_latencies) if self.all_latencies else 0.0
            max_latency = max(self.all_latencies) if self.all_latencies else 0.0

            return {
                "total_queries": total,
                "cache_hits": hits,
                "cache_misses": misses,
                "hit_ratio": round(ratio, 1),
                "avg_response_time": round(avg_all, 2),
                "avg_hit_time": round(avg_hit, 2),
                "avg_miss_time": round(avg_miss, 2),
                "min_response_time": round(min_latency, 2),
                "max_response_time": round(max_latency, 2),
                "history_count": len(self.history),
            }

    def get_history(self, limit: int = 100, reverse: bool = True) -> List[QueryHistoryItem]:
        """Return history items, latest first if reverse is True."""
        with self._lock:
            items = list(self.history)
        if reverse:
            items.reverse()
        return items[:limit]

    def get_chart_data(self) -> Dict[str, Any]:
        """Return raw data suitable for Matplotlib rendering."""
        with self._lock:
            return {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "indices": [item.index for item in self.history],
                "latencies": [item.response_time_ms for item in self.history],
                "is_hits": [item.is_cache_hit for item in self.history],
                "domains": [item.domain for item in self.history],
            }

    def clear_history(self):
        """Clear query history log without clearing cumulative counters."""
        with self._lock:
            self.history.clear()

    def reset_all(self):
        """Reset all statistical counters and history."""
        with self._lock:
            self.total_queries = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.all_latencies.clear()
            self.hit_latencies.clear()
            self.miss_latencies.clear()
            self.history.clear()
            self._next_history_id = 1

    def export_csv(self, filepath: Path) -> Tuple[bool, str]:
        """Export query history to a CSV file."""
        with self._lock:
            if not self.history:
                return False, "History is currently empty."
            items = [item.to_dict() for item in self.history]

        try:
            with open(filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "index",
                        "timestamp",
                        "domain",
                        "record_type",
                        "hit_status",
                        "response_time_ms",
                        "status",
                        "server",
                        "records",
                        "ttl",
                    ],
                )
                writer.writeheader()
                writer.writerows(items)
            return True, f"Successfully exported {len(items)} queries to CSV."
        except Exception as e:
            return False, f"Failed to export CSV: {e}"

    def export_json(self, filepath: Path) -> Tuple[bool, str]:
        """Export query history and aggregated stats to JSON."""
        with self._lock:
            data = {
                "summary": self.get_summary(),
                "history": [item.to_dict() for item in self.history],
            }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True, f"Successfully exported history and metrics to JSON."
        except Exception as e:
            return False, f"Failed to export JSON: {e}"

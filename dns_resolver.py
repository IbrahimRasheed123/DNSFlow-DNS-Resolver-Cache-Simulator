"""
DNS Resolver Service for DNS Resolver & Cache Simulator.
Performs real DNS lookups using dnspython, manages cache hits/misses,
and measures exact response times in milliseconds.
"""

import re
import time
from typing import Optional, List, Tuple
import dns.resolver
import dns.exception

from config import DEFAULT_DNS_TIMEOUT, DEFAULT_DNS_LIFETIME
from models import DNSQueryResult
from dns_cache import DNSCache


class DNSResolverService:
    """
    High-level DNS Resolver Service.
    Coordinates between the local DNSCache and real recursive DNS servers.
    """

    def __init__(self, cache: Optional[DNSCache] = None):
        self.cache = cache or DNSCache()

    @staticmethod
    def validate_domain(domain: str) -> Tuple[bool, str]:
        """Validate basic domain name syntax."""
        cleaned = DNSCache.normalize_domain(domain)
        if not cleaned:
            return False, "Domain name cannot be empty."

        if len(cleaned) > 253:
            return False, "Domain name exceeds maximum length of 253 characters."

        # Regex for valid domain labels (letters, digits, hyphens)
        pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        # Also allow localhost or single test labels if needed, but standard FQDN matches:
        if not (re.match(pattern, cleaned) or cleaned in ("localhost", "local")):
            return False, "Invalid domain format. Example: google.com or mail.yahoo.co.uk"

        return True, cleaned

    def resolve(
        self,
        domain: str,
        record_type: str = "A",
        upstream_ip: Optional[str] = None,
        server_label: str = "System Default",
        demo_ttl: int = 0,
        bypass_cache: bool = False,
    ) -> DNSQueryResult:
        """
        Execute full resolution workflow:
        1. Check local cache (unless bypassed)
        2. If HIT: return cached records with remaining TTL instantly
        3. If MISS: query upstream DNS via dnspython, store in cache, return result
        """
        is_valid, validation_msg = self.validate_domain(domain)
        if not is_valid:
            return DNSQueryResult(
                domain=domain.strip(),
                record_type=record_type.upper(),
                status="INVALID_DOMAIN",
                error_message=validation_msg,
                response_time_ms=0.0,
                resolution_path=["Client", "Validation Failed"],
            )

        norm_domain = validation_msg
        rec_type = record_type.strip().upper()

        # Step 1: Cache Check (if not bypassed)
        if not bypass_cache:
            entry, is_hit = self.cache.get(norm_domain, rec_type)
            if is_hit and entry:
                # Ultra-fast local memory lookup simulation (0.2 - 1.2 ms)
                start_clock = time.perf_counter()
                records = list(entry.records)
                remaining = entry.remaining_ttl()
                elapsed_ms = max(0.1, (time.perf_counter() - start_clock) * 1000.0)

                return DNSQueryResult(
                    domain=norm_domain,
                    record_type=rec_type,
                    records=records,
                    original_ttl=entry.original_ttl,
                    effective_ttl=entry.configured_ttl,
                    remaining_ttl=remaining,
                    response_time_ms=elapsed_ms,
                    is_cache_hit=True,
                    upstream_server=f"{entry.upstream_server} (Cached)",
                    status="SUCCESS",
                    error_message=None,
                    resolution_path=[
                        "Client Request",
                        "Local DNS Cache [CACHE HIT]",
                        "Client Response (Instant)",
                    ],
                )

        # Step 2: Cache Miss -> Perform Real DNS Resolution
        resolver = dns.resolver.Resolver()
        resolver.timeout = DEFAULT_DNS_TIMEOUT
        resolver.lifetime = DEFAULT_DNS_LIFETIME

        server_display = server_label
        if upstream_ip:
            try:
                resolver.nameservers = [upstream_ip]
                server_display = f"{server_label} ({upstream_ip})"
            except Exception as e:
                return DNSQueryResult(
                    domain=norm_domain,
                    record_type=rec_type,
                    status="CONFIG_ERROR",
                    error_message=f"Invalid upstream DNS IP: {e}",
                    response_time_ms=0.0,
                    resolution_path=["Client", "Resolver Config Error"],
                )

        start_time = time.perf_counter()
        try:
            answer = resolver.resolve(norm_domain, rec_type)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            # Extract formatted record strings
            records: List[str] = []
            for rdata in answer:
                text_val = rdata.to_text()
                # Clean up quotes from TXT records
                if rec_type == "TXT" and text_val.startswith('"') and text_val.endswith('"'):
                    text_val = text_val[1:-1]
                records.append(text_val)

            # Retrieve authoritative TTL from the answer RRset
            authoritative_ttl = int(answer.rrset.ttl) if answer.rrset else 300

            # Cache the freshly resolved records
            new_entry = self.cache.put(
                domain=norm_domain,
                record_type=rec_type,
                records=records,
                original_ttl=authoritative_ttl,
                upstream_server=server_display,
                demo_ttl=demo_ttl if demo_ttl > 0 else None,
            )

            return DNSQueryResult(
                domain=norm_domain,
                record_type=rec_type,
                records=records,
                original_ttl=authoritative_ttl,
                effective_ttl=new_entry.configured_ttl,
                remaining_ttl=new_entry.remaining_ttl(),
                response_time_ms=elapsed_ms,
                is_cache_hit=False,
                upstream_server=server_display,
                status="SUCCESS",
                error_message=None,
                resolution_path=[
                    "Client Request",
                    "Local DNS Cache [CACHE MISS]",
                    "DNS Resolver",
                    f"Upstream Server [{server_display}]",
                    "DNS Response Received",
                    "Stored in Local Cache",
                    "Client Response Delivered",
                ],
            )

        except dns.resolver.NXDOMAIN:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return DNSQueryResult(
                domain=norm_domain,
                record_type=rec_type,
                records=[],
                response_time_ms=elapsed_ms,
                is_cache_hit=False,
                upstream_server=server_display,
                status="NXDOMAIN",
                error_message=f"Non-Existent Domain (NXDOMAIN): '{norm_domain}' does not exist.",
                resolution_path=[
                    "Client Request",
                    "Local DNS Cache [CACHE MISS]",
                    f"Upstream Server [{server_display}]",
                    "NXDOMAIN (Domain not found)",
                ],
            )

        except dns.resolver.NoAnswer:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return DNSQueryResult(
                domain=norm_domain,
                record_type=rec_type,
                records=[],
                response_time_ms=elapsed_ms,
                is_cache_hit=False,
                upstream_server=server_display,
                status="NO_ANSWER",
                error_message=f"No {rec_type} record found for '{norm_domain}'.",
                resolution_path=[
                    "Client Request",
                    "Local DNS Cache [CACHE MISS]",
                    f"Upstream Server [{server_display}]",
                    f"No {rec_type} Record",
                ],
            )

        except dns.resolver.Timeout:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return DNSQueryResult(
                domain=norm_domain,
                record_type=rec_type,
                records=[],
                response_time_ms=elapsed_ms,
                is_cache_hit=False,
                upstream_server=server_display,
                status="TIMEOUT",
                error_message=f"Query timed out while contacting {server_display}.",
                resolution_path=[
                    "Client Request",
                    "Local DNS Cache [CACHE MISS]",
                    f"Upstream Server [{server_display}] [TIMEOUT]",
                ],
            )

        except dns.resolver.NoNameservers:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return DNSQueryResult(
                domain=norm_domain,
                record_type=rec_type,
                records=[],
                response_time_ms=elapsed_ms,
                is_cache_hit=False,
                upstream_server=server_display,
                status="SERVER_FAILURE",
                error_message="All nameservers failed or refused query response (SERVFAIL).",
                resolution_path=[
                    "Client Request",
                    "Local DNS Cache [CACHE MISS]",
                    f"Upstream Server [{server_display}] [SERVFAIL]",
                ],
            )

        except dns.exception.DNSException as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return DNSQueryResult(
                domain=norm_domain,
                record_type=rec_type,
                records=[],
                response_time_ms=elapsed_ms,
                is_cache_hit=False,
                upstream_server=server_display,
                status="DNS_ERROR",
                error_message=f"DNS resolution error: {str(e)}",
                resolution_path=["Client Request", "Resolver Error"],
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return DNSQueryResult(
                domain=norm_domain,
                record_type=rec_type,
                records=[],
                response_time_ms=elapsed_ms,
                is_cache_hit=False,
                upstream_server=server_display,
                status="ERROR",
                error_message=f"System error: {str(e)}",
                resolution_path=["Client Request", "System Exception"],
            )

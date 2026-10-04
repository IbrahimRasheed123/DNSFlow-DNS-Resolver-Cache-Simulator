"""
Configuration module for DNS Resolver & DNS Cache Simulator.
Contains application settings, DNS server presets, supported record types,
color palettes, and default constants.
"""

import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SCREENSHOTS_DIR = BASE_DIR / "screenshots"

DATA_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_EXPORT_CSV = DATA_DIR / "query_history.csv"
HISTORY_EXPORT_JSON = DATA_DIR / "query_history.json"
CACHE_EXPORT_JSON = DATA_DIR / "cache_dump.json"

# Application Metadata
APP_NAME = "DNS Resolver & DNS Cache Simulator"
APP_VERSION = "2.0.0"
APP_SUBTITLE = "Computer Networks Simulation & Visual Analysis Tool"
AUTHOR = "Computer Networks Laboratory"

# DNS Server Presets
DNS_SERVERS = {
    "System Default": None,
    "Google Public DNS (8.8.8.8)": "8.8.8.8",
    "Cloudflare DNS (1.1.1.1)": "1.1.1.1",
    "Quad9 Secure (9.9.9.9)": "9.9.9.9",
    "OpenDNS (208.67.222.222)": "208.67.222.222",
    "Custom IP...": "custom",
}

# Supported DNS Record Types
RECORD_TYPES = ["A", "AAAA", "CNAME", "MX", "NS", "TXT", "SOA", "PTR"]

RECORD_DESCRIPTIONS = {
    "A": "IPv4 Address (32-bit address mapping)",
    "AAAA": "IPv6 Address (128-bit address mapping)",
    "CNAME": "Canonical Name (Domain alias redirection)",
    "MX": "Mail Exchange (Mail server routing with priority)",
    "NS": "Name Server (Authoritative DNS servers for zone)",
    "TXT": "Text Record (Verification, SPF, DKIM, DMARC)",
    "SOA": "Start of Authority (Zone administration metadata)",
    "PTR": "Pointer Record (Reverse DNS lookup IP to domain)",
}

# Demo TTL Presets (Seconds)
# When set to 0, use the real authoritative TTL from DNS response
TTL_MODES = {
    "Real DNS TTL (Authoritative)": 0,
    "10 Seconds (Demo / Fast Expiry)": 10,
    "30 Seconds (Presentation Mode)": 30,
    "60 Seconds (1 Minute Test)": 60,
    "120 Seconds (2 Minutes Test)": 120,
}

# Quick Domain Suggestions for rapid testing
QUICK_DOMAINS = [
    "google.com",
    "github.com",
    "cloudflare.com",
    "wikipedia.org",
    "amazon.com",
    "microsoft.com",
]

# Network Timeouts
DEFAULT_DNS_TIMEOUT = 4.0  # seconds
DEFAULT_DNS_LIFETIME = 5.0  # seconds

# Theme & Palette Definition (Dark & Light Friendly)
THEME_COLORS = {
    "dark": {
        "bg_primary": "#0b0f19",       # Deep slate-black
        "bg_secondary": "#111827",     # Dark slate
        "bg_card": "#1f2937",          # Slate gray card
        "bg_card_highlight": "#374151",# Lighter hover card
        "border": "#374151",           # Slate border
        "text_primary": "#f9fafb",     # Pure white text
        "text_secondary": "#9ca3af",   # Subdued gray text
        "accent": "#0284c7",           # Sky 600
        "accent_hover": "#0369a1",     # Sky 700
        "cyan": "#06b6d4",             # Cyan 500
        "hit": "#10b981",              # Emerald green (CACHE HIT)
        "hit_bg": "#064e3b",           # Dark emerald background
        "miss": "#f59e0b",             # Amber orange (CACHE MISS)
        "miss_bg": "#78350f",          # Dark amber background
        "error": "#ef4444",            # Crimson red (Error/NXDOMAIN)
        "error_bg": "#7f1d1d",         # Dark crimson background
        "chart_bg": "#111827",
    },
    "light": {
        "bg_primary": "#f8fafc",
        "bg_secondary": "#f1f5f9",
        "bg_card": "#ffffff",
        "bg_card_highlight": "#e2e8f0",
        "border": "#cbd5e1",
        "text_primary": "#0f172a",
        "text_secondary": "#64748b",
        "accent": "#0284c7",
        "accent_hover": "#0369a1",
        "cyan": "#0891b2",
        "hit": "#059669",
        "hit_bg": "#d1fae5",
        "miss": "#d97706",
        "miss_bg": "#fef3c7",
        "error": "#dc2626",
        "error_bg": "#fee2e2",
        "chart_bg": "#ffffff",
    },
}

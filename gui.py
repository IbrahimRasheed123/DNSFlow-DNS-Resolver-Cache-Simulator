"""
GUI Module for DNS Resolver & DNS Cache Simulator.
Built with CustomTkinter and embedded Matplotlib for high-performance visual analysis.
Features:
- Dark/Modern Cyber Networking Dashboard
- Real-time Resolution Flow Visualizer (Client -> Cache -> Resolver -> Server -> Response)
- Live TTL countdown table with expiration alerts
- Query History with CSV/JSON export
- Interactive Matplotlib Latency and Hit/Miss Analytics
- Multi-threaded asynchronous queries for non-blocking UI
"""

import sys
import time
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any

import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

# Matplotlib embedding
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from config import (
    APP_NAME,
    APP_VERSION,
    APP_SUBTITLE,
    DNS_SERVERS,
    RECORD_TYPES,
    RECORD_DESCRIPTIONS,
    TTL_MODES,
    QUICK_DOMAINS,
    THEME_COLORS,
    HISTORY_EXPORT_CSV,
    HISTORY_EXPORT_JSON,
    CACHE_EXPORT_JSON,
)
from models import DNSQueryResult, CacheEntry
from dns_cache import DNSCache
from dns_resolver import DNSResolverService
from statistics import StatsManager


class DNSAppGUI:
    """Main Desktop Application GUI Controller."""

    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1340x890")
        self.root.minsize(1150, 760)

        # Appearance configuration
        self.current_theme = "dark"
        ctk.set_appearance_mode(self.current_theme)
        ctk.set_default_color_theme("blue")

        # Core logic services
        self.cache = DNSCache()
        self.resolver = DNSResolverService(cache=self.cache)
        self.stats = StatsManager()

        # UI State Variables
        self.is_resolving = False
        self.selected_server_key = tk.StringVar(value="Google Public DNS (8.8.8.8)")
        self.custom_server_ip = tk.StringVar(value="")
        self.selected_record_type = tk.StringVar(value="A")
        self.selected_ttl_mode = tk.StringVar(value="Real DNS TTL (Authoritative)")
        self.cache_search_query = tk.StringVar(value="")
        self.last_query_result: Optional[DNSQueryResult] = None

        # Build GUI Components
        self._build_header()
        self._build_top_dashboard()
        self._build_stats_ribbon()
        self._build_main_tabview()
        self._build_status_footer()

        # Start Background TTL Countdown Watcher (runs every 1000ms)
        self._schedule_ttl_tick()

    # =========================================================================
    # GUI LAYOUT BUILDERS
    # =========================================================================

    def _build_header(self):
        """Build top navigation header with title and global controls."""
        header = ctk.CTkFrame(self.root, corner_radius=0, height=65, fg_color=("#1e293b", "#0f172a"))
        header.pack(fill="x", side="top", padx=0, pady=0)

        # Left Branding
        brand_frame = ctk.CTkFrame(header, fg_color="transparent")
        brand_frame.pack(side="left", padx=16, pady=8)

        title_label = ctk.CTkLabel(
            brand_frame,
            text=f"🌐 {APP_NAME.upper()}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#38bdf8",
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            brand_frame,
            text=f"{APP_SUBTITLE} • v{APP_VERSION}",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
        )
        subtitle_label.pack(anchor="w")

        # Right Global Options
        options_frame = ctk.CTkFrame(header, fg_color="transparent")
        options_frame.pack(side="right", padx=16, pady=8)

        # Upstream DNS Selector
        ctk.CTkLabel(options_frame, text="DNS Server:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(8, 4))
        self.server_dropdown = ctk.CTkOptionMenu(
            options_frame,
            values=list(DNS_SERVERS.keys()),
            variable=self.selected_server_key,
            command=self._on_server_change,
            width=220,
            dynamic_resizing=False,
        )
        self.server_dropdown.pack(side="left", padx=4)

        # Custom IP entry (hidden unless custom selected)
        self.custom_ip_entry = ctk.CTkEntry(
            options_frame,
            placeholder_text="Enter IP (e.g. 1.1.1.1)",
            textvariable=self.custom_server_ip,
            width=140,
        )

        # Demo TTL selector
        ctk.CTkLabel(options_frame, text="TTL Mode:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(12, 4))
        self.ttl_dropdown = ctk.CTkOptionMenu(
            options_frame,
            values=list(TTL_MODES.keys()),
            variable=self.selected_ttl_mode,
            width=200,
            dynamic_resizing=False,
        )
        self.ttl_dropdown.pack(side="left", padx=4)

        # Theme Switch
        self.theme_switch = ctk.CTkSwitch(
            options_frame,
            text="Dark Mode",
            command=self._toggle_theme,
            font=ctk.CTkFont(size=12),
        )
        self.theme_switch.select()
        self.theme_switch.pack(side="left", padx=(14, 4))

    def _build_top_dashboard(self):
        """Build upper section: Query inputs, resolution flow, and response card."""
        dashboard = ctk.CTkFrame(self.root, fg_color="transparent")
        dashboard.pack(fill="x", padx=16, pady=(10, 6))

        # Split into Left (Query Form) and Right (Flow & Response)
        dashboard.grid_columnconfigure(0, weight=4)
        dashboard.grid_columnconfigure(1, weight=6)

        # ----------------- LEFT: Query Form Card -----------------
        query_card = ctk.CTkFrame(dashboard, corner_radius=10, fg_color=("#f1f5f9", "#1e293b"))
        query_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=0)

        ctk.CTkLabel(
            query_card,
            text="🔍 DNS Query Formulation",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#0284c7",
        ).pack(anchor="w", padx=14, pady=(12, 4))

        # Domain Input Field
        domain_box = ctk.CTkFrame(query_card, fg_color="transparent")
        domain_box.pack(fill="x", padx=14, pady=4)

        ctk.CTkLabel(domain_box, text="Domain Name:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        self.domain_entry = ctk.CTkEntry(
            domain_box,
            placeholder_text="Enter domain (e.g. google.com, github.com)...",
            height=36,
            font=ctk.CTkFont(size=13),
        )
        self.domain_entry.pack(fill="x")
        self.domain_entry.insert(0, "google.com")
        self.domain_entry.bind("<Return>", lambda event: self.start_resolution())

        # Quick preset chips
        preset_frame = ctk.CTkFrame(query_card, fg_color="transparent")
        preset_frame.pack(fill="x", padx=14, pady=(2, 8))
        ctk.CTkLabel(preset_frame, text="Quick Presets:", font=ctk.CTkFont(size=11), text_color="#94a3b8").pack(side="left", padx=(0, 6))
        for d in QUICK_DOMAINS[:4]:
            btn = ctk.CTkButton(
                preset_frame,
                text=d,
                width=65,
                height=22,
                font=ctk.CTkFont(size=10),
                fg_color=("#e2e8f0", "#334155"),
                text_color=("#0f172a", "#f8fafc"),
                hover_color="#0284c7",
                command=lambda domain=d: self._set_domain_and_resolve(domain),
            )
            btn.pack(side="left", padx=2)

        # Record Type Selector
        type_box = ctk.CTkFrame(query_card, fg_color="transparent")
        type_box.pack(fill="x", padx=14, pady=4)
        ctk.CTkLabel(type_box, text="DNS Record Type:", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        
        self.record_type_seg = ctk.CTkSegmentedButton(
            type_box,
            values=["A", "AAAA", "CNAME", "MX", "NS", "TXT"],
            variable=self.selected_record_type,
            selected_color="#0284c7",
            selected_hover_color="#0369a1",
        )
        self.record_type_seg.pack(fill="x")

        # Action Buttons
        btn_frame = ctk.CTkFrame(query_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=14, pady=(12, 12))

        self.resolve_btn = ctk.CTkButton(
            btn_frame,
            text="⚡ RESOLVE DNS",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self.start_resolution,
        )
        self.resolve_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.recheck_btn = ctk.CTkButton(
            btn_frame,
            text="🔄 Re-Query (Test Hit)",
            font=ctk.CTkFont(size=12),
            height=38,
            width=140,
            fg_color="#10b981",
            hover_color="#059669",
            command=self._query_again_for_hit,
        )
        self.recheck_btn.pack(side="left", padx=4)

        self.fast_test_btn = ctk.CTkButton(
            btn_frame,
            text="⏳ 10s Demo Test",
            font=ctk.CTkFont(size=12),
            height=38,
            width=120,
            fg_color="#f59e0b",
            hover_color="#d97706",
            command=self._run_demo_10s_test,
        )
        self.fast_test_btn.pack(side="left", padx=(4, 0))

        # ----------------- RIGHT: Flow Visualizer & Response -----------------
        right_panel = ctk.CTkFrame(dashboard, corner_radius=10, fg_color=("#f1f5f9", "#1e293b"))
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=0)

        # Visual Pipeline Header
        flow_header = ctk.CTkFrame(right_panel, fg_color="transparent")
        flow_header.pack(fill="x", padx=14, pady=(10, 4))
        ctk.CTkLabel(
            flow_header,
            text="🚀 Resolution Flow Visualizer",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#0284c7",
        ).pack(side="left")

        self.flow_mode_badge = ctk.CTkLabel(
            flow_header,
            text="IDLE / READY",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#334155",
            corner_radius=6,
            text_color="#f8fafc",
            padx=10,
            pady=2,
        )
        self.flow_mode_badge.pack(side="right")

        # Stage Boxes Pipeline Container
        self.stage_pipeline = ctk.CTkFrame(right_panel, fg_color=("#e2e8f0", "#111827"), corner_radius=8)
        self.stage_pipeline.pack(fill="x", padx=14, pady=4)

        # Create the 5 Stage Cards
        self.stage_widgets: Dict[str, Dict[str, Any]] = {}
        stages = [
            ("stage_client", "1. CLIENT\n(Request)"),
            ("stage_cache", "2. CACHE\n(Lookup)"),
            ("stage_resolver", "3. RESOLVER\n(dnspython)"),
            ("stage_server", "4. SERVER\n(8.8.8.8)"),
            ("stage_response", "5. RESPONSE\n(Delivery)"),
        ]

        stage_box = ctk.CTkFrame(self.stage_pipeline, fg_color="transparent")
        stage_box.pack(fill="x", padx=8, pady=8)

        for i, (key, label) in enumerate(stages):
            card = ctk.CTkFrame(stage_box, corner_radius=6, fg_color="#1e293b", width=105, height=54)
            card.pack(side="left", expand=True, fill="both", padx=2)
            card.pack_propagate(False)

            lbl = ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=10, weight="bold"), text_color="#cbd5e1")
            lbl.pack(expand=True, pady=2)

            badge = ctk.CTkLabel(card, text="WAITING", font=ctk.CTkFont(size=8, weight="bold"), text_color="#94a3b8")
            badge.pack(side="bottom", pady=(0, 4))

            self.stage_widgets[key] = {"frame": card, "label": lbl, "badge": badge}

            if i < len(stages) - 1:
                arrow = ctk.CTkLabel(stage_box, text="➔", font=ctk.CTkFont(size=12, weight="bold"), text_color="#64748b")
                arrow.pack(side="left", padx=1)

        # Flow Explanation / Narrative Banner
        self.flow_narrative = ctk.CTkLabel(
            right_panel,
            text="Enter a domain above and click 'RESOLVE DNS' to observe real-time resolution and cache dynamics.",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
            wraplength=600,
            justify="left",
        )
        self.flow_narrative.pack(fill="x", padx=14, pady=(2, 4))

        # Response Details Frame
        response_box = ctk.CTkFrame(right_panel, fg_color=("#e2e8f0", "#0f172a"), corner_radius=8)
        response_box.pack(fill="both", expand=True, padx=14, pady=(4, 10))

        resp_top = ctk.CTkFrame(response_box, fg_color="transparent")
        resp_top.pack(fill="x", padx=10, pady=(6, 2))

        self.resp_status_badge = ctk.CTkLabel(
            resp_top,
            text="STANDBY",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#475569",
            corner_radius=6,
            text_color="#f8fafc",
            padx=12,
            pady=2,
        )
        self.resp_status_badge.pack(side="left")

        self.resp_metrics_label = ctk.CTkLabel(
            resp_top,
            text="Latency: -- ms | TTL: -- | Server: --",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94a3b8",
        )
        self.resp_metrics_label.pack(side="left", padx=12)

        copy_btn = ctk.CTkButton(
            resp_top,
            text="📋 Copy Records",
            width=100,
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color=("#cbd5e1", "#334155"),
            text_color=("#0f172a", "#f8fafc"),
            command=self._copy_response_to_clipboard,
        )
        copy_btn.pack(side="right")

        # Records Display Box
        self.records_textbox = ctk.CTkTextbox(
            response_box,
            height=60,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=("#ffffff", "#1e293b"),
            text_color=("#0f172a", "#38bdf8"),
            wrap="none",
        )
        self.records_textbox.pack(fill="both", expand=True, padx=10, pady=(2, 8))
        self.records_textbox.insert("1.0", "Resolved DNS records will be printed here...")
        self.records_textbox.configure(state="disabled")

    def _build_stats_ribbon(self):
        """Build horizontal row of 6 analytical performance statistic cards."""
        ribbon = ctk.CTkFrame(self.root, fg_color="transparent")
        ribbon.pack(fill="x", padx=16, pady=4)

        # Configure 6 columns evenly
        for i in range(6):
            ribbon.grid_columnconfigure(i, weight=1)

        self.stat_cards = {}
        card_configs = [
            ("total", "📊 Total Queries", "0", "#38bdf8", "All DNS requests processed"),
            ("hits", "🟢 Cache Hits", "0", "#10b981", "Served directly from RAM"),
            ("misses", "🟠 Cache Misses", "0", "#f59e0b", "Resolved via upstream DNS"),
            ("ratio", "🎯 Cache Hit Ratio", "0.0%", "#06b6d4", "(Hits / Total Queries) × 100"),
            ("cached", "💾 Cached Records", "0 Active", "#a855f7", "Currently in local memory"),
            ("latency", "⚡ Avg Response Time", "0.0 ms", "#ec4899", "Overall network latency"),
        ]

        for idx, (key, title, val, color, tooltip) in enumerate(card_configs):
            card = ctk.CTkFrame(ribbon, corner_radius=8, fg_color=("#f1f5f9", "#1e293b"))
            card.grid(row=0, column=idx, sticky="nsew", padx=3, pady=0)

            lbl_title = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color="#94a3b8")
            lbl_title.pack(anchor="w", padx=8, pady=(6, 0))

            lbl_val = ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=18, weight="bold"), text_color=color)
            lbl_val.pack(anchor="w", padx=8, pady=(0, 2))

            lbl_sub = ctk.CTkLabel(card, text=tooltip, font=ctk.CTkFont(size=9), text_color="#64748b")
            lbl_sub.pack(anchor="w", padx=8, pady=(0, 6))

            self.stat_cards[key] = lbl_val

    def _build_main_tabview(self):
        """Build main bottom tabview containing Cache, History, Analytics, and Theory."""
        self.tabview = ctk.CTkTabview(self.root, corner_radius=10, fg_color=("#f1f5f9", "#1e293b"))
        self.tabview.pack(fill="both", expand=True, padx=16, pady=(4, 6))

        self.tab_cache = self.tabview.add("🗄️ DNS Cache Table")
        self.tab_history = self.tabview.add("📜 Query History")
        self.tab_charts = self.tabview.add("📈 Latency & Hit/Miss Charts")
        self.tab_theory = self.tabview.add("📘 How DNS Caching Works")

        self._build_tab_cache()
        self._build_tab_history()
        self._build_tab_charts()
        self._build_tab_theory()

    # ----------------- TAB 1: CACHE TABLE -----------------
    def _build_tab_cache(self):
        """Construct the interactive live cache table tab."""
        # Top toolbar
        toolbar = ctk.CTkFrame(self.tab_cache, fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=(6, 6))

        ctk.CTkLabel(toolbar, text="Filter Cache:", font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(0, 4))
        self.cache_filter_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="Search domain / record type...",
            textvariable=self.cache_search_query,
            width=200,
            height=28,
        )
        self.cache_filter_entry.pack(side="left", padx=4)
        self.cache_filter_entry.bind("<KeyRelease>", lambda e: self.refresh_cache_table())

        btn_refresh = ctk.CTkButton(
            toolbar,
            text="🔄 Refresh",
            width=80,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#0284c7",
            command=self.refresh_cache_table,
        )
        btn_refresh.pack(side="left", padx=4)

        btn_purge = ctk.CTkButton(
            toolbar,
            text="⚡ Purge Expired",
            width=110,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#d97706",
            command=self._purge_expired_cache,
        )
        btn_purge.pack(side="left", padx=4)

        btn_clear = ctk.CTkButton(
            toolbar,
            text="🗑️ Clear Entire Cache",
            width=130,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#ef4444",
            hover_color="#b91c1c",
            command=self._clear_cache_confirmed,
        )
        btn_clear.pack(side="left", padx=4)

        self.cache_summary_lbl = ctk.CTkLabel(
            toolbar,
            text="0 Active / 0 Expired records",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38bdf8",
        )
        self.cache_summary_lbl.pack(side="right", padx=10)

        # Cache Table Column Headers
        header_frame = ctk.CTkFrame(self.tab_cache, height=28, fg_color=("#e2e8f0", "#111827"), corner_radius=6)
        header_frame.pack(fill="x", padx=10, pady=(2, 2))

        cols = [
            ("Domain", 220),
            ("Type", 70),
            ("Resolved Value(s)", 350),
            ("Orig TTL", 90),
            ("Remaining TTL", 130),
            ("Status", 100),
            ("Added At", 90),
            ("Actions", 140),
        ]
        for name, width in cols:
            lbl = ctk.CTkLabel(
                header_frame,
                text=name,
                width=width,
                font=ctk.CTkFont(size=11, weight="bold"),
                anchor="w" if name != "Actions" else "center",
                text_color="#94a3b8",
            )
            lbl.pack(side="left", padx=4)

        # Scrollable Cache Table Container
        self.cache_rows_container = ctk.CTkScrollableFrame(
            self.tab_cache,
            fg_color=("#ffffff", "#111827"),
            corner_radius=6,
        )
        self.cache_rows_container.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        self.refresh_cache_table()

    # ----------------- TAB 2: QUERY HISTORY -----------------
    def _build_tab_history(self):
        """Construct the query history tab with CSV and JSON exports."""
        toolbar = ctk.CTkFrame(self.tab_history, fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=(6, 6))

        btn_clear_hist = ctk.CTkButton(
            toolbar,
            text="🗑️ Clear History",
            width=110,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#ef4444",
            hover_color="#b91c1c",
            command=self._clear_history_confirmed,
        )
        btn_clear_hist.pack(side="left", padx=4)

        btn_export_csv = ctk.CTkButton(
            toolbar,
            text="📥 Export CSV",
            width=100,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#10b981",
            hover_color="#059669",
            command=self._export_history_csv,
        )
        btn_export_csv.pack(side="left", padx=4)

        btn_export_json = ctk.CTkButton(
            toolbar,
            text="📥 Export JSON",
            width=100,
            height=28,
            font=ctk.CTkFont(size=11),
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self._export_history_json,
        )
        btn_export_json.pack(side="left", padx=4)

        self.history_count_lbl = ctk.CTkLabel(
            toolbar,
            text="Total History: 0 queries",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94a3b8",
        )
        self.history_count_lbl.pack(side="right", padx=10)

        # Header Row
        header_frame = ctk.CTkFrame(self.tab_history, height=28, fg_color=("#e2e8f0", "#111827"), corner_radius=6)
        header_frame.pack(fill="x", padx=10, pady=(2, 2))

        cols = [
            ("#", 45),
            ("Time", 80),
            ("Domain", 220),
            ("Type", 70),
            ("Result", 110),
            ("Latency", 95),
            ("Server", 180),
            ("Resolved Records", 340),
        ]
        for name, width in cols:
            lbl = ctk.CTkLabel(
                header_frame,
                text=name,
                width=width,
                font=ctk.CTkFont(size=11, weight="bold"),
                anchor="w",
                text_color="#94a3b8",
            )
            lbl.pack(side="left", padx=4)

        # Scrollable History Container
        self.history_rows_container = ctk.CTkScrollableFrame(
            self.tab_history,
            fg_color=("#ffffff", "#111827"),
            corner_radius=6,
        )
        self.history_rows_container.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        self.refresh_history_table()

    # ----------------- TAB 3: CHARTS & ANALYTICS -----------------
    def _build_tab_charts(self):
        """Construct the Matplotlib-powered performance analytics tab."""
        chart_top = ctk.CTkFrame(self.tab_charts, fg_color="transparent")
        chart_top.pack(fill="x", padx=10, pady=(4, 4))

        ctk.CTkLabel(
            chart_top,
            text="📊 Real-Time Response Time & Cache Performance Analytics",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38bdf8",
        ).pack(side="left")

        btn_refresh_charts = ctk.CTkButton(
            chart_top,
            text="🔄 Refresh Charts",
            width=120,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#0284c7",
            command=self.update_charts,
        )
        btn_refresh_charts.pack(side="right")

        # Container Frame for Matplotlib Canvas
        self.chart_container = ctk.CTkFrame(self.tab_charts, fg_color=("#ffffff", "#111827"), corner_radius=8)
        self.chart_container.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        # Initial Matplotlib Figure
        self.fig, (self.ax_latency, self.ax_pie) = plt.subplots(1, 2, figsize=(10, 3.5), dpi=95)
        self.fig.patch.set_facecolor("#111827")
        self.fig.tight_layout(pad=3.0)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_container)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True, padx=4, pady=4)

        self.update_charts()

    # ----------------- TAB 4: EDUCATIONAL THEORY -----------------
    def _build_tab_theory(self):
        """Construct the educational concept reference guide for presentations & viva."""
        guide_box = ctk.CTkScrollableFrame(self.tab_theory, fg_color=("#ffffff", "#111827"), corner_radius=8)
        guide_box.pack(fill="both", expand=True, padx=10, pady=8)

        theory_text = (
            "📌 COMPUTER NETWORKS LAB PROJECT: DNS RESOLVER & CACHE SIMULATOR\n"
            "====================================================================\n\n"
            "1. WHAT IS DNS (DOMAIN NAME SYSTEM)?\n"
            "   DNS is the fundamental address-resolution directory of the Internet (RFC 1034 / RFC 1035).\n"
            "   It translates human-friendly domain names (e.g. google.com) into machine-routable IP addresses\n"
            "   (e.g. 142.250.190.46 for IPv4 or 2607:f8b0:4005:805::200e for IPv6).\n\n"
            "2. THE RESOLUTION WORKFLOW & CACHE MECHANISM:\n"
            "   When an application requests resolution of a domain name:\n\n"
            "   Step A: Local Cache Inspection\n"
            "   ------------------------------\n"
            "   The resolver checks its local cache indexed by (Domain + Record Type).\n"
            "   • If entry exists AND Remaining TTL > 0  ==>  [CACHE HIT]\n"
            "     Result returned instantaneously from RAM (< 1 millisecond)!\n"
            "     No packets traverse external internet networks. High bandwidth & root server load savings.\n\n"
            "   • If entry missing OR Remaining TTL <= 0 ==>  [CACHE MISS]\n"
            "     The resolver must perform recursive lookup contacting external DNS servers.\n"
            "     Network traversal introduces latency (20ms - 200ms depending on RTT).\n"
            "     Upon response, the record is stored in local cache with TTL for subsequent queries.\n\n"
            "3. UNDERSTANDING TTL (TIME TO LIVE):\n"
            "   • TTL is an unsigned 32-bit integer representing seconds a record may be cached.\n"
            "   • Set by authoritative nameservers to balance performance versus agility.\n"
            "   • Short TTL (e.g. 60s): Fast propagation of IP changes (useful for CDN / failover).\n"
            "   • Long TTL (e.g. 86400s / 1 day): Maximum cache efficiency and lowest query load.\n"
            "   • Demo TTL Mode in this app allows demonstrating cache expiration within seconds.\n\n"
            "4. KEY RECORD TYPES SUPPORTED:\n"
            "   • A: IPv4 Address mapping (32-bit)\n"
            "   • AAAA: IPv6 Address mapping (128-bit)\n"
            "   • CNAME: Canonical Name (alias to another domain name)\n"
            "   • MX: Mail Exchange (specifies mail servers with integer priority)\n"
            "   • NS: Name Server (delegates a DNS zone to authoritative nameservers)\n"
            "   • TXT: Arbitrary text data (used for SPF, DKIM, DMARC, domain verification)\n\n"
            "5. PERFORMANCE IMPLICATIONS OBSERVED IN THIS SIMULATOR:\n"
            "   • Cache Hit Latency: ~0.1 ms - 1.5 ms\n"
            "   • Cache Miss Latency: ~30 ms - 150 ms\n"
            "   • Speedup Factor: 50x to 300x faster response time for cached domains!\n"
        )

        theory_label = ctk.CTkLabel(
            guide_box,
            text=theory_text,
            font=ctk.CTkFont(family="Consolas", size=12),
            justify="left",
            anchor="w",
            text_color=("#0f172a", "#f8fafc"),
        )
        theory_label.pack(anchor="w", padx=14, pady=10)

    def _build_status_footer(self):
        """Build status bar at bottom of window."""
        footer = ctk.CTkFrame(self.root, height=28, fg_color=("#1e293b", "#0f172a"), corner_radius=0)
        footer.pack(fill="x", side="bottom")

        self.footer_status_lbl = ctk.CTkLabel(
            footer,
            text="System Ready. Enter domain to resolve.",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
        )
        self.footer_status_lbl.pack(side="left", padx=16)

        footer_right = ctk.CTkLabel(
            footer,
            text="Python 3.12 • CustomTkinter • dnspython • Matplotlib",
            font=ctk.CTkFont(size=10),
            text_color="#64748b",
        )
        footer_right.pack(side="right", padx=16)

    # =========================================================================
    # EVENT HANDLERS & CORE ACTIONS
    # =========================================================================

    def _on_server_change(self, choice: str):
        """Handle change in upstream DNS server selection."""
        if choice == "Custom IP...":
            self.custom_ip_entry.pack(side="left", padx=4)
        else:
            self.custom_ip_entry.pack_forget()

    def _toggle_theme(self):
        """Switch between dark and light themes dynamically."""
        if self.theme_switch.get() == 1:
            self.current_theme = "dark"
            ctk.set_appearance_mode("dark")
            self.fig.patch.set_facecolor("#111827")
        else:
            self.current_theme = "light"
            ctk.set_appearance_mode("light")
            self.fig.patch.set_facecolor("#ffffff")
        self.update_charts()

    def _set_domain_and_resolve(self, domain: str):
        """Preset chip clicked: populate domain and trigger resolution."""
        self.domain_entry.delete(0, "end")
        self.domain_entry.insert(0, domain)
        self.start_resolution()

    def _query_again_for_hit(self):
        """Re-query the current domain to immediately test CACHE HIT."""
        self.start_resolution()

    def _run_demo_10s_test(self):
        """One-click demo mode: sets TTL to 10s demo mode, resolves, starts countdown."""
        self.selected_ttl_mode.set("10 Seconds (Demo / Fast Expiry)")
        self.start_resolution()

    def start_resolution(self):
        """Initiate asynchronous DNS resolution in background worker thread."""
        if self.is_resolving:
            return

        domain = self.domain_entry.get().strip()
        record_type = self.selected_record_type.get().strip()

        if not domain:
            messagebox.showwarning("Input Required", "Please enter a valid domain name (e.g. google.com).")
            return

        # Upstream DNS server calculation
        server_choice = self.selected_server_key.get()
        if server_choice == "Custom IP...":
            custom_ip = self.custom_server_ip.get().strip()
            if not custom_ip:
                messagebox.showerror("Error", "Please enter custom DNS server IP address.")
                return
            upstream_ip = custom_ip
            server_label = f"Custom ({custom_ip})"
        else:
            upstream_ip = DNS_SERVERS.get(server_choice)
            server_label = server_choice

        # Demo TTL calculation
        ttl_mode_str = self.selected_ttl_mode.get()
        demo_ttl = TTL_MODES.get(ttl_mode_str, 0)

        # Set UI to resolving state
        self.is_resolving = True
        self.resolve_btn.configure(state="disabled", text="⏳ RESOLVING...")
        self.footer_status_lbl.configure(text=f"Resolving '{domain}' ({record_type}) via {server_label}...")

        # Visual pipeline: highlight stage 1 (Client) and stage 2 (Cache)
        self._highlight_pipeline_stage("stage_client", "#38bdf8", "ACTIVE")
        self._highlight_pipeline_stage("stage_cache", "#f59e0b", "CHECKING...")
        self._reset_stage("stage_resolver")
        self._reset_stage("stage_server")
        self._reset_stage("stage_response")

        # Launch worker thread
        threading.Thread(
            target=self._resolve_worker,
            args=(domain, record_type, upstream_ip, server_label, demo_ttl),
            daemon=True,
        ).start()

    def _resolve_worker(
        self,
        domain: str,
        record_type: str,
        upstream_ip: Optional[str],
        server_label: str,
        demo_ttl: int,
    ):
        """Worker thread executing DNS lookup logic safely outside GUI thread."""
        time.sleep(0.05)  # slight pause so visual highlight is visible
        result = self.resolver.resolve(
            domain=domain,
            record_type=record_type,
            upstream_ip=upstream_ip,
            server_label=server_label,
            demo_ttl=demo_ttl,
        )

        # Post results back to main thread
        self.root.after(0, lambda: self._on_resolution_complete(result))

    def _on_resolution_complete(self, result: DNSQueryResult):
        """Main thread callback when DNS query completes."""
        self.is_resolving = False
        self.resolve_btn.configure(state="normal", text="⚡ RESOLVE DNS")
        self.last_query_result = result

        # Record in statistics
        self.stats.record_query(result)

        # Update Visual Flow Pipeline
        self._render_flow_pipeline(result)

        # Update Response Card
        self._render_response_card(result)

        # Update Statistics Ribbon
        self._update_stats_ribbon()

        # Update Tables & Charts
        self.refresh_cache_table()
        self.refresh_history_table()
        self.update_charts()

        # Update status footer
        if result.is_cache_hit:
            self.footer_status_lbl.configure(
                text=f"CACHE HIT: '{result.domain}' ({result.record_type}) served from local memory in {result.response_time_ms:.2f} ms."
            )
        elif result.is_success:
            self.footer_status_lbl.configure(
                text=f"CACHE MISS: '{result.domain}' ({result.record_type}) resolved in {result.response_time_ms:.2f} ms via {result.upstream_server}."
            )
        else:
            self.footer_status_lbl.configure(
                text=f"Lookup failed for '{result.domain}': {result.error_message}"
            )

    # =========================================================================
    # VISUAL FLOW & RESPONSE RENDERING
    # =========================================================================

    def _highlight_pipeline_stage(self, stage_key: str, color: str, badge_text: str):
        """Set glowing color and status badge for a stage in pipeline."""
        if stage_key in self.stage_widgets:
            widget = self.stage_widgets[stage_key]
            widget["frame"].configure(fg_color=color)
            widget["badge"].configure(text=badge_text, text_color="#ffffff")

    def _reset_stage(self, stage_key: str):
        """Reset a stage to dimmed idle state."""
        if stage_key in self.stage_widgets:
            widget = self.stage_widgets[stage_key]
            widget["frame"].configure(fg_color="#1e293b")
            widget["badge"].configure(text="WAITING", text_color="#94a3b8")

    def _dim_bypassed_stage(self, stage_key: str):
        """Dim stage that was bypassed due to Cache Hit."""
        if stage_key in self.stage_widgets:
            widget = self.stage_widgets[stage_key]
            widget["frame"].configure(fg_color="#0f172a")
            widget["badge"].configure(text="BYPASSED", text_color="#64748b")

    def _render_flow_pipeline(self, result: DNSQueryResult):
        """Visualize resolution steps according to Cache Hit vs Cache Miss."""
        if result.is_cache_hit:
            # CACHE HIT FLOW: Client -> Cache (HIT) -> Response (Bypasses Resolver & Server)
            self.flow_mode_badge.configure(text="🎯 CACHE HIT FLOW", fg_color="#065f46", text_color="#34d399")
            self._highlight_pipeline_stage("stage_client", "#0284c7", "REQUEST")
            self._highlight_pipeline_stage("stage_cache", "#10b981", "HIT (RAM)")
            self._dim_bypassed_stage("stage_resolver")
            self._dim_bypassed_stage("stage_server")
            self._highlight_pipeline_stage("stage_response", "#10b981", f"{result.response_time_ms:.1f}ms")

            self.flow_narrative.configure(
                text=f"🎯 CACHE HIT: '{result.domain}' found in local cache! Bypassed resolver & upstream DNS servers. "
                     f"Served from RAM in {result.response_time_ms:.2f} ms (Remaining TTL: {result.remaining_ttl}s).",
                text_color="#34d399",
            )
        else:
            # CACHE MISS FLOW: Client -> Cache (MISS) -> Resolver -> Server -> Response
            if result.is_success:
                self.flow_mode_badge.configure(text="🌐 CACHE MISS FLOW", fg_color="#78350f", text_color="#fbbf24")
                self._highlight_pipeline_stage("stage_client", "#0284c7", "REQUEST")
                self._highlight_pipeline_stage("stage_cache", "#f59e0b", "MISS")
                self._highlight_pipeline_stage("stage_resolver", "#0284c7", "QUERYING")
                self._highlight_pipeline_stage("stage_server", "#0284c7", "RESOLVED")
                self._highlight_pipeline_stage("stage_response", "#f59e0b", f"{result.response_time_ms:.1f}ms")

                self.flow_narrative.configure(
                    text=f"🌐 CACHE MISS: '{result.domain}' not found in local cache or expired. Forwarded to {result.upstream_server}. "
                         f"Response received in {result.response_time_ms:.2f} ms, cached with TTL {result.effective_ttl}s.",
                    text_color="#fbbf24",
                )
            else:
                self.flow_mode_badge.configure(text=f"⚠️ {result.status}", fg_color="#7f1d1d", text_color="#f87171")
                self._highlight_pipeline_stage("stage_client", "#0284c7", "REQUEST")
                self._highlight_pipeline_stage("stage_cache", "#f59e0b", "MISS")
                self._highlight_pipeline_stage("stage_resolver", "#ef4444", "FAILED")
                self._highlight_pipeline_stage("stage_server", "#ef4444", "NO REPLY")
                self._highlight_pipeline_stage("stage_response", "#ef4444", "ERROR")

                self.flow_narrative.configure(
                    text=f"❌ RESOLUTION ERROR: {result.error_message}",
                    text_color="#f87171",
                )

    def _render_response_card(self, result: DNSQueryResult):
        """Render response status, latency, TTL, and records."""
        if result.is_cache_hit:
            self.resp_status_badge.configure(text="🟢 CACHE HIT", fg_color="#10b981", text_color="#ffffff")
        elif result.is_success:
            self.resp_status_badge.configure(text="🟠 CACHE MISS", fg_color="#f59e0b", text_color="#ffffff")
        else:
            self.resp_status_badge.configure(text=f"🔴 {result.status}", fg_color="#ef4444", text_color="#ffffff")

        metrics_txt = (
            f"Latency: {result.response_time_ms:.2f} ms  |  "
            f"TTL: {result.remaining_ttl if result.is_cache_hit else result.effective_ttl}s  |  "
            f"Server: {result.upstream_server}"
        )
        self.resp_metrics_label.configure(text=metrics_txt)

        self.records_textbox.configure(state="normal")
        self.records_textbox.delete("1.0", "end")

        if result.is_success and result.records:
            lines = [f"• {rec}" for rec in result.records]
            self.records_textbox.insert("1.0", "\n".join(lines))
        elif result.error_message:
            self.records_textbox.insert("1.0", f"Error details:\n{result.error_message}")
        else:
            self.records_textbox.insert("1.0", "No answer records returned.")

        self.records_textbox.configure(state="disabled")

    def _copy_response_to_clipboard(self):
        """Copy records from response textbox to OS clipboard."""
        if self.last_query_result and self.last_query_result.records:
            text_to_copy = "\n".join(self.last_query_result.records)
            self.root.clipboard_clear()
            self.root.clipboard_append(text_to_copy)
            messagebox.showinfo("Copied", "Resolved DNS records copied to clipboard!")
        else:
            messagebox.showwarning("Notice", "No records available to copy.")

    # =========================================================================
    # STATISTICS & METRICS
    # =========================================================================

    def _update_stats_ribbon(self):
        """Update top 6 summary metric cards."""
        summary = self.stats.get_summary()
        active_cache = self.cache.get_active_count()
        total_cache = self.cache.get_total_count()

        self.stat_cards["total"].configure(text=str(summary["total_queries"]))
        self.stat_cards["hits"].configure(text=str(summary["cache_hits"]))
        self.stat_cards["misses"].configure(text=str(summary["cache_misses"]))
        self.stat_cards["ratio"].configure(text=f"{summary['hit_ratio']}%")
        self.stat_cards["cached"].configure(text=f"{active_cache} Active ({total_cache} total)")
        self.stat_cards["latency"].configure(text=f"{summary['avg_response_time']} ms")

    # =========================================================================
    # CACHE TABLE & REAL-TIME COUNTDOWN
    # =========================================================================

    def refresh_cache_table(self):
        """Re-render cache entries in Tab 1 based on current cache state and search filter."""
        # Clear existing rows
        for widget in self.cache_rows_container.winfo_children():
            widget.destroy()

        query = self.cache_search_query.get().strip().lower()
        entries = self.cache.get_all(include_expired=True)

        if query:
            entries = [
                e for e in entries
                if query in e.domain.lower() or query in e.record_type.lower()
            ]

        active_count = self.cache.get_active_count()
        expired_count = self.cache.get_expired_count()
        self.cache_summary_lbl.configure(
            text=f"{active_count} Active / {expired_count} Expired records"
        )

        if not entries:
            empty_lbl = ctk.CTkLabel(
                self.cache_rows_container,
                text="Local DNS Cache is currently empty. Resolve any domain above to populate cache entries.",
                font=ctk.CTkFont(size=12, slant="italic"),
                text_color="#64748b",
            )
            empty_lbl.pack(pady=30)
            return

        for entry in entries:
            self._render_cache_row(entry)

    def _render_cache_row(self, entry: CacheEntry):
        """Render a single cache entry row."""
        is_expired = entry.is_expired()
        rem_ttl = entry.remaining_ttl()

        row = ctk.CTkFrame(
            self.cache_rows_container,
            fg_color=("#f8fafc", "#1f2937") if not is_expired else ("#fef2f2", "#271c1c"),
            corner_radius=4,
            height=32,
        )
        row.pack(fill="x", pady=2)

        # Domain
        ctk.CTkLabel(
            row,
            text=entry.domain,
            width=220,
            anchor="w",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f8fafc" if self.current_theme == "dark" else "#0f172a",
        ).pack(side="left", padx=4)

        # Record Type
        ctk.CTkLabel(
            row,
            text=entry.record_type,
            width=70,
            anchor="w",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38bdf8",
        ).pack(side="left", padx=4)

        # Resolved Value Preview
        ctk.CTkLabel(
            row,
            text=entry.records_summary(max_items=2),
            width=350,
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color="#cbd5e1" if self.current_theme == "dark" else "#475569",
        ).pack(side="left", padx=4)

        # Original TTL
        ctk.CTkLabel(
            row,
            text=f"{entry.original_ttl}s",
            width=90,
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
        ).pack(side="left", padx=4)

        # Remaining TTL (live countdown)
        ttl_display = f"{rem_ttl}s remaining" if not is_expired else "0s (Expired)"
        ttl_color = "#10b981" if rem_ttl > 10 else ("#f59e0b" if rem_ttl > 0 else "#ef4444")
        ctk.CTkLabel(
            row,
            text=ttl_display,
            width=130,
            anchor="w",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=ttl_color,
        ).pack(side="left", padx=4)

        # Status badge
        badge_text = "ACTIVE" if not is_expired else "EXPIRED"
        badge_color = "#065f46" if not is_expired else "#7f1d1d"
        badge_fg = "#34d399" if not is_expired else "#f87171"
        badge = ctk.CTkLabel(
            row,
            text=badge_text,
            width=90,
            corner_radius=4,
            fg_color=badge_color,
            text_color=badge_fg,
            font=ctk.CTkFont(size=10, weight="bold"),
        )
        badge.pack(side="left", padx=4)

        # Added time
        ctk.CTkLabel(
            row,
            text=entry.created_at_formatted(),
            width=90,
            anchor="w",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
        ).pack(side="left", padx=4)

        # Actions: Query Again & Delete
        action_frame = ctk.CTkFrame(row, fg_color="transparent", width=140)
        action_frame.pack(side="left", padx=4)

        btn_q = ctk.CTkButton(
            action_frame,
            text="Query",
            width=58,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color="#0284c7",
            command=lambda d=entry.domain, t=entry.record_type: self._query_from_table(d, t),
        )
        btn_q.pack(side="left", padx=2)

        btn_d = ctk.CTkButton(
            action_frame,
            text="Delete",
            width=58,
            height=22,
            font=ctk.CTkFont(size=10),
            fg_color="#ef4444",
            hover_color="#b91c1c",
            command=lambda d=entry.domain, t=entry.record_type: self._delete_cache_entry(d, t),
        )
        btn_d.pack(side="left", padx=2)

    def _query_from_table(self, domain: str, record_type: str):
        """Action button to immediately query a specific cached item."""
        self.domain_entry.delete(0, "end")
        self.domain_entry.insert(0, domain)
        self.selected_record_type.set(record_type)
        self.start_resolution()

    def _delete_cache_entry(self, domain: str, record_type: str):
        """Remove a specific item from the local cache."""
        self.cache.delete(domain, record_type)
        self.refresh_cache_table()
        self._update_stats_ribbon()

    def _purge_expired_cache(self):
        """Remove all expired cache entries."""
        count = self.cache.purge_expired()
        self.refresh_cache_table()
        self._update_stats_ribbon()
        messagebox.showinfo("Purge Complete", f"Purged {count} expired record(s) from cache.")

    def _clear_cache_confirmed(self):
        """Prompt user confirmation and clear entire cache."""
        if messagebox.askyesno("Clear Cache", "Are you sure you want to clear all cached DNS records?"):
            count = self.cache.clear()
            self.refresh_cache_table()
            self._update_stats_ribbon()
            messagebox.showinfo("Cache Cleared", f"Cleared {count} record(s) from DNS cache.")

    def _schedule_ttl_tick(self):
        """Timer ticking every 1000ms (1 second) to refresh TTL countdowns."""
        try:
            if not self.root.winfo_exists():
                return
            self._tick_ttl()
            self._ttl_timer_id = self.root.after(1000, self._schedule_ttl_tick)
        except Exception:
            pass

    def on_closing(self):
        """Clean shutdown handler to cancel pending event timers and close window."""
        if hasattr(self, "_ttl_timer_id") and self._ttl_timer_id:
            try:
                self.root.after_cancel(self._ttl_timer_id)
            except Exception:
                pass
        try:
            plt.close(self.fig)
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def _tick_ttl(self):
        """Refresh remaining TTLs in cache table if user has tab active."""
        try:
            if not self.root.winfo_exists():
                return
            # Only refresh visible widgets if cache has items to save CPU
            if self.cache.get_total_count() > 0:
                if self.tabview.get() == "🗄️ DNS Cache Table":
                    self.refresh_cache_table()
                self._update_stats_ribbon()
        except Exception:
            pass

    # =========================================================================
    # QUERY HISTORY TABLE & EXPORTS
    # =========================================================================

    def refresh_history_table(self):
        """Re-render query history table in Tab 2."""
        for widget in self.history_rows_container.winfo_children():
            widget.destroy()

        history_items = self.stats.get_history(limit=100, reverse=True)
        self.history_count_lbl.configure(text=f"Total History: {len(self.stats.history)} queries")

        if not history_items:
            empty_lbl = ctk.CTkLabel(
                self.history_rows_container,
                text="No queries recorded yet. Resolved queries will be logged here with timestamps and latencies.",
                font=ctk.CTkFont(size=12, slant="italic"),
                text_color="#64748b",
            )
            empty_lbl.pack(pady=30)
            return

        for item in history_items:
            row = ctk.CTkFrame(
                self.history_rows_container,
                fg_color=("#f8fafc", "#1f2937"),
                corner_radius=4,
                height=30,
            )
            row.pack(fill="x", pady=2)

            # Index
            ctk.CTkLabel(row, text=f"#{item.index}", width=45, anchor="w", font=ctk.CTkFont(size=11), text_color="#94a3b8").pack(side="left", padx=4)

            # Timestamp
            ctk.CTkLabel(row, text=item.timestamp_str, width=80, anchor="w", font=ctk.CTkFont(size=11), text_color="#94a3b8").pack(side="left", padx=4)

            # Domain
            ctk.CTkLabel(
                row,
                text=item.domain,
                width=220,
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#f8fafc" if self.current_theme == "dark" else "#0f172a",
            ).pack(side="left", padx=4)

            # Type
            ctk.CTkLabel(row, text=item.record_type, width=70, anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color="#38bdf8").pack(side="left", padx=4)

            # Result Badge
            if item.is_cache_hit:
                res_bg, res_fg, res_txt = "#065f46", "#34d399", "CACHE HIT"
            elif item.status == "SUCCESS":
                res_bg, res_fg, res_txt = "#78350f", "#fbbf24", "CACHE MISS"
            else:
                res_bg, res_fg, res_txt = "#7f1d1d", "#f87171", item.status

            badge = ctk.CTkLabel(
                row,
                text=res_txt,
                width=100,
                corner_radius=4,
                fg_color=res_bg,
                text_color=res_fg,
                font=ctk.CTkFont(size=10, weight="bold"),
            )
            badge.pack(side="left", padx=4)

            # Latency
            lat_color = "#10b981" if item.is_cache_hit else "#f59e0b"
            ctk.CTkLabel(row, text=f"{item.response_time_ms:.2f} ms", width=95, anchor="w", font=ctk.CTkFont(size=11, weight="bold"), text_color=lat_color).pack(side="left", padx=4)

            # Server
            ctk.CTkLabel(row, text=item.server[:22], width=180, anchor="w", font=ctk.CTkFont(size=11), text_color="#94a3b8").pack(side="left", padx=4)

            # Records preview
            ctk.CTkLabel(row, text=item.records_preview, width=340, anchor="w", font=ctk.CTkFont(size=11), text_color="#cbd5e1" if self.current_theme == "dark" else "#475569").pack(side="left", padx=4)

    def _clear_history_confirmed(self):
        """Prompt user confirmation and clear history."""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear query history?"):
            self.stats.clear_history()
            self.refresh_history_table()
            self.update_charts()

    def _export_history_csv(self):
        """Export history log to CSV file."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All Files", "*.*")],
            initialdir=str(HISTORY_EXPORT_CSV.parent),
            initialfile="dns_query_history.csv",
        )
        if filepath:
            success, msg = self.stats.export_csv(Path(filepath))
            if success:
                messagebox.showinfo("Export Successful", msg)
            else:
                messagebox.showerror("Export Failed", msg)

    def _export_history_json(self):
        """Export history and metrics summary to JSON file."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All Files", "*.*")],
            initialdir=str(HISTORY_EXPORT_JSON.parent),
            initialfile="dns_query_history.json",
        )
        if filepath:
            success, msg = self.stats.export_json(Path(filepath))
            if success:
                messagebox.showinfo("Export Successful", msg)
            else:
                messagebox.showerror("Export Failed", msg)

    # =========================================================================
    # MATPLOTLIB ANALYTICS CHARTS
    # =========================================================================

    def update_charts(self):
        """Redraw Latency comparison and Hit/Miss Donut charts."""
        self.ax_latency.clear()
        self.ax_pie.clear()

        # Visual styling constants
        is_dark = self.current_theme == "dark"
        bg_col = "#111827" if is_dark else "#ffffff"
        text_col = "#f8fafc" if is_dark else "#0f172a"
        grid_col = "#374151" if is_dark else "#e2e8f0"

        chart_data = self.stats.get_chart_data()
        indices = chart_data["indices"]
        latencies = chart_data["latencies"]
        is_hits = chart_data["is_hits"]
        hits_count = chart_data["hits"]
        miss_count = chart_data["misses"]

        # ---------------- Chart 1: Latency Timeline ----------------
        self.ax_latency.set_facecolor(bg_col)
        self.ax_latency.tick_params(colors=text_col, labelsize=9)
        self.ax_latency.grid(True, linestyle="--", alpha=0.35, color=grid_col)

        for spine in self.ax_latency.spines.values():
            spine.set_color(grid_col)

        self.ax_latency.set_title("Response Latency per Query (ms)", color=text_col, fontsize=11, fontweight="bold")
        self.ax_latency.set_xlabel("Query Sequence Index", color=text_col, fontsize=9)
        self.ax_latency.set_ylabel("Latency (ms)", color=text_col, fontsize=9)

        if indices:
            # Line connection
            self.ax_latency.plot(indices, latencies, color="#0284c7", alpha=0.5, linestyle="-", linewidth=1.5, zorder=1)

            # Scatter points color-coded: Green for hits, Orange for misses
            hit_x = [indices[i] for i, h in enumerate(is_hits) if h]
            hit_y = [latencies[i] for i, h in enumerate(is_hits) if h]
            miss_x = [indices[i] for i, h in enumerate(is_hits) if not h]
            miss_y = [latencies[i] for i, h in enumerate(is_hits) if not h]

            if hit_x:
                self.ax_latency.scatter(hit_x, hit_y, color="#10b981", s=50, label="Cache Hit (<2ms)", zorder=3)
            if miss_x:
                self.ax_latency.scatter(miss_x, miss_y, color="#f59e0b", s=50, label="Cache Miss (Network)", zorder=3)

            legend = self.ax_latency.legend(facecolor=bg_col, edgecolor=grid_col, fontsize=8)
            for text in legend.get_texts():
                text.set_color(text_col)
        else:
            self.ax_latency.text(
                0.5, 0.5, "No query data yet.\nExecute queries to see live latency plot.",
                ha="center", va="center", transform=self.ax_latency.transAxes,
                color="#64748b", fontsize=10, style="italic"
            )

        # ---------------- Chart 2: Hit vs Miss Donut Chart ----------------
        self.ax_pie.set_facecolor(bg_col)

        total = hits_count + miss_count
        if total > 0:
            sizes = [hits_count, miss_count]
            labels = [f"Hits ({hits_count})", f"Misses ({miss_count})"]
            colors = ["#10b981", "#f59e0b"]

            # Filter zero slices
            active_slices = [(s, l, c) for s, l, c in zip(sizes, labels, colors) if s > 0]
            curr_sizes = [x[0] for x in active_slices]
            curr_labels = [x[1] for x in active_slices]
            curr_colors = [x[2] for x in active_slices]

            wedges, texts, autotexts = self.ax_pie.pie(
                curr_sizes,
                labels=curr_labels,
                colors=curr_colors,
                autopct="%1.1f%%",
                startangle=140,
                pctdistance=0.75,
                textprops=dict(color=text_col, fontsize=9, fontweight="bold"),
                wedgeprops=dict(width=0.45, edgecolor=bg_col),
            )
            for at in autotexts:
                at.set_color("#ffffff")
                at.set_fontsize(10)

            ratio = (hits_count / total) * 100.0
            self.ax_pie.text(
                0, 0, f"{ratio:.1f}%\nHit Ratio",
                ha="center", va="center",
                color="#38bdf8", fontsize=11, fontweight="bold"
            )
            self.ax_pie.set_title("Cache Hit vs Miss Distribution", color=text_col, fontsize=11, fontweight="bold")
        else:
            self.ax_pie.text(
                0.5, 0.5, "No query data yet.\nExecute queries to see Hit/Miss ratio.",
                ha="center", va="center", transform=self.ax_pie.transAxes,
                color="#64748b", fontsize=10, style="italic"
            )
            self.ax_pie.set_title("Cache Hit vs Miss Distribution", color=text_col, fontsize=11, fontweight="bold")

        self.fig.tight_layout(pad=2.5)
        self.canvas.draw_idle()

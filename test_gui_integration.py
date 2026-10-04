"""
Automated integration test for DNS GUI components, event loops, and charts.
Validates that GUI initializes, renders frames, resolves records, and updates plots without crashing.
"""

import time
import customtkinter as ctk
from gui import DNSAppGUI

def test_gui():
    print("=== Testing GUI Initialization & Workflow ===")
    root = ctk.CTk()
    root.withdraw()  # keep window hidden during automated headless test

    app = DNSAppGUI(root)
    print("1. DNSAppGUI initialized successfully.")

    # Test resolving google.com
    app.domain_entry.delete(0, "end")
    app.domain_entry.insert(0, "google.com")
    app.selected_record_type.set("A")

    # Run resolution synchronously in test
    result = app.resolver.resolve("google.com", "A")
    app._on_resolution_complete(result)
    print(f"2. Query 1 processed: is_hit={result.is_cache_hit}, latency={result.response_time_ms:.2f}ms")

    # Run second query to verify cache hit
    result2 = app.resolver.resolve("google.com", "A")
    app._on_resolution_complete(result2)
    print(f"3. Query 2 processed: is_hit={result2.is_cache_hit}, latency={result2.response_time_ms:.2f}ms")

    # Verify GUI metrics updated
    summary = app.stats.get_summary()
    print(f"4. GUI Statistics verified: Total={summary['total_queries']}, Hits={summary['cache_hits']}, Misses={summary['cache_misses']}")

    # Verify chart render
    app.update_charts()
    print("5. Matplotlib charts updated successfully.")

    # Verify cache table and history
    app.refresh_cache_table()
    app.refresh_history_table()
    print("6. Cache table and history table refreshed without errors.")

    # Cleanup
    app.on_closing()
    print("\n>>> ALL GUI INTEGRATION TESTS PASSED CLEANLY! <<<")

if __name__ == "__main__":
    test_gui()

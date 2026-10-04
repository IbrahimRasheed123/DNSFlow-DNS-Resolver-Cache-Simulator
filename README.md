# 🌐 DNS Resolver & DNS Cache Simulator

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/GUI-CustomTkinter-1f6feb)](https://github.com/TomSchimansky/CustomTkinter)
[![DNS Engine](https://img.shields.io/badge/DNS-dnspython-brightgreen)](https://www.dnspython.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A complete, high-performance **Computer Networks desktop application** built with **Python, CustomTkinter, dnspython, and Matplotlib**. This tool visually demonstrates the inner workings of **DNS Resolution**, **Local Cache Hierarchies**, **TTL Management**, and **Hit/Miss Latency Performance** through an interactive, cyber-modern dashboard.

---

## 📸 Overview & Resolution Workflow

When a client queries a domain name (e.g., `google.com`), the simulator executes the fundamental DNS caching algorithm:

```text
User Request
     │
     ▼
[ Cache Check ] ──(Entry present & TTL > 0?)
     │                                    │
    YES                                  NO
     │                                    │
     ▼                                    ▼
[ CACHE HIT ]                      [ CACHE MISS ]
Serve instantly from RAM (<1ms)    Recursive lookup via Upstream DNS
Bypass internet queries            Traverse external network (20-150ms)
                                          │
                                          ▼
                                   [ Store in Cache ]
                                   Save with TTL for next query
```

---

## ✨ Features

- **⚡ Real DNS Lookups**: Resolves real-world domain names against authoritative/recursive nameservers using `dnspython`.
- **🎯 Visual CACHE HIT / CACHE MISS Indicator**: Glowing status badges and real-time narrative explaining resolution paths.
- **🚀 5-Stage Pipeline Visualizer**:
  - `CLIENT` ➔ `CACHE` ➔ `RESOLVER` ➔ `UPSTREAM SERVER` ➔ `RESPONSE`
  - Dynamically highlights active stages or dims bypassed stages on cache hits.
- **📋 Supported Record Types**: `A` (IPv4), `AAAA` (IPv6), `CNAME` (Aliases), `MX` (Mail Servers), `NS` (Name Servers), `TXT` (SPF/DKIM), `SOA`, and `PTR`.
- **⏳ TTL Management & Fast Demo Mode**:
  - Displays remaining TTL with a **live real-time 1-second countdown**.
  - Automatically transitions records from `ACTIVE` to `EXPIRED`.
  - **Demo TTL Mode (10s, 30s, 60s, 120s)** enables quick demonstrations of cache expiration without waiting for hours.
- **🌐 Configurable Upstream DNS**:
  - System Default Resolver
  - Google Public DNS (`8.8.8.8`)
  - Cloudflare DNS (`1.1.1.1`)
  - Quad9 Secure DNS (`9.9.9.9`)
  - OpenDNS (`208.67.222.222`)
  - Custom IP entry
- **📊 Real-Time Analytics & Matplotlib Charts**:
  - Interactive **Latency Timeline plot** comparing Cache Hit (<1ms) vs Cache Miss (30-150ms).
  - Dynamic **Cache Hit vs Miss Donut Chart** with percentage ratio.
- **📈 6 Key Performance Metric Cards**:
  - Total Queries, Cache Hits, Cache Misses, Hit Ratio %, Active Cache Count, and Average Response Time.
- **📜 Query History & Data Export**:
  - Comprehensive history log with timestamps, latencies, and servers.
  - One-click export to **CSV** and **JSON** formats.
- **🎨 Sleek Cyber / Modern Theme**:
  - Built with CustomTkinter. Supports **Dark Mode** and **Light Mode**.
- **🧵 Non-Blocking Asynchronous Threading**:
  - All network operations run in background worker threads; GUI remains silky-smooth at 60 FPS.

---

## 📂 Project Structure

```text
DNS-Resolver-Cache-Simulator/
├── main.py                     # Application bootstrap & entry point
├── gui.py                      # CustomTkinter dashboard & flow visualizer
├── dns_resolver.py             # DNS lookup engine & latency measurement
├── dns_cache.py                # Thread-safe in-memory cache & TTL manager
├── models.py                   # Data models (CacheEntry, DNSQueryResult)
├── statistics.py               # Statistics counter & CSV/JSON exporter
├── config.py                   # Presets, color palettes, record mappings
├── test_suite.py               # 11 automated unit & integration tests
├── test_core.py                # Core engine verification test
├── test_gui_integration.py     # Headless GUI event loop test
├── seed_sample_data.py         # Sample data generation script
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
├── CN_PROJECT_REPORT.md        # Complete academic report
├── PRESENTATION_SLIDES.md      # Presentation slide deck
├── VIVA_QUESTIONS_AND_ANSWERS.md # 25 Viva Voce Q&As
├── data/                       # Exported history & cache files
│   ├── query_history.csv
│   ├── query_history.json
│   └── cache_dump.json
└── screenshots/                # Application screenshots
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python **3.10+** (Python 3.12 recommended)
- Windows, macOS, or Linux
- Active Internet connection for real DNS queries

### Step-by-Step Setup (Windows / VS Code)

1. **Open Terminal / Command Prompt** in the project directory:
   ```powershell
   cd "C:\Users\IBRAHIM\.gemini\antigravity-ide\scratch\DNS-Resolver-Cache-Simulator"
   ```

2. **(Optional) Create a Python Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Verify Dependencies**:
   ```powershell
   python -c "import dns.resolver, customtkinter, matplotlib; print('Dependencies OK!')"
   ```

5. **Run the Application**:
   ```powershell
   python main.py
   ```

---

## 🧪 Testing Procedure & Test Cases

Run the automated test suite covering all 11 networking specifications:
```powershell
python test_suite.py
```

### Verified Test Cases:
| Test ID | Objective | Expected Result | Status |
| :--- | :--- | :--- | :---: |
| **TC-01** | First Query `google.com` (A) | Cache Miss, queries network, populates cache | **PASS** |
| **TC-02** | Immediate Re-Query `google.com` | Cache Hit, response latency < 2ms | **PASS** |
| **TC-03** | IPv6 `AAAA` Record Query | Successfully extracts IPv6 address records | **PASS** |
| **TC-04** | Mail Server `MX` Query | Resolves MX priority and mail server hostnames | **PASS** |
| **TC-05** | Text Record `TXT` Query | Resolves SPF / verification strings | **PASS** |
| **TC-06** | Custom Upstream Nameserver | Routes lookup through `1.1.1.1` | **PASS** |
| **TC-07** | Invalid Domain Handling | Gracefully catches `NXDOMAIN` without crashing | **PASS** |
| **TC-08** | Demo TTL Expiration (1s/10s) | Entry expires; subsequent query is a Cache Miss | **PASS** |
| **TC-09** | Cache Purge & Deletion | Removes expired records and single key entries | **PASS** |
| **TC-10** | Statistics & Hit Ratio Formula | `Hit Ratio = (Hits / Total) × 100` mathematically verified | **PASS** |
| **TC-11** | CSV & JSON Exports | Valid files generated with accurate schemas | **PASS** |

---

## 🎯 How to Demonstrate in a Project Presentation

1. **Demonstrate Cache Miss (Network Lookup)**:
   - Enter `google.com`, select Record Type `A`, click **"RESOLVE DNS"**.
   - Point out the **CACHE MISS (Amber)** badge, latency (~30-100 ms), and the full 5-stage pipeline.
2. **Demonstrate Cache Hit (RAM Lookup)**:
   - Click **"🔄 Re-Query (Test Hit)"**.
   - Point out the instant **CACHE HIT (Green)** badge, near-zero latency (~0.1-1.0 ms), and note how stages 3 and 4 were **BYPASSED**.
3. **Demonstrate TTL Expiration (Fast Demo)**:
   - Select TTL Mode: **"10 Seconds (Demo / Fast Expiry)"**.
   - Enter `example.com` and resolve.
   - Switch to **🗄️ DNS Cache Table** tab. Watch the live **Remaining TTL count down: 10s ➔ 9s ➔ ... ➔ 0s (Expired)**.
   - Re-query `example.com` once expired. Observe that it triggers a **fresh CACHE MISS**!
4. **Showcase Visual Analytics**:
   - Navigate to **📈 Latency & Hit/Miss Charts** tab.
   - Showcase the Matplotlib response time scatter plot illustrating the 100x latency reduction of caching.
5. **Export Data**:
   - Navigate to **📜 Query History** tab and click **"Export CSV"** or **"Export JSON"**.

---

## 📜 Educational Documentation Included

- **[CN Project Report](CN_PROJECT_REPORT.md)**: 15-page comprehensive academic report covering RFCs, mathematical modeling, and benchmark analysis.
- **[Presentation Slides](PRESENTATION_SLIDES.md)**: 12 ready-to-present PowerPoint slides with speaker notes.
- **[Viva Questions & Answers](VIVA_QUESTIONS_AND_ANSWERS.md)**: 25 in-depth technical viva questions with model answers.

---

## ⚖️ License
Released under the MIT License. Designed for Computer Networks laboratory education and demonstrations.

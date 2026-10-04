# 🎓 COMPREHENSIVE VIVA VOCE QUESTIONS & ANSWERS
## Project: DNS Resolver & DNS Cache Simulator
**Domain:** Computer Networks (Application Layer, Transport Layer, Address Resolution)

---

### **Q1: What is DNS and which layer of the OSI model does it operate at?**
**Answer:**  
DNS (Domain Name System) operates at the **Application Layer (Layer 7)** of the OSI model and TCP/IP protocol suite. Its primary objective is to map human-friendly Fully Qualified Domain Names (e.g., `google.com`) to numerical IP addresses (e.g., `142.250.190.46`), allowing network routers and transport protocols to establish connections.

---

### **Q2: Does DNS use UDP or TCP, and on which port?**
**Answer:**  
DNS uses **Port 53**. It primarily uses **UDP** for standard client queries and responses because:
1. Low latency: UDP has no 3-way handshake overhead.
2. Lightweight packets: Most standard DNS request/response messages fit within the historical 512-byte UDP limit (extended to 4096 bytes via EDNS0).

However, DNS uses **TCP** in two critical scenarios:
1. **Zone Transfers:** Between primary and secondary nameservers (AXFR/IXFR), where reliability and ordering are crucial.
2. **Truncated Responses:** When a response exceeds the maximum UDP packet size (TC bit set to 1 in the header), prompting the client to re-issue the query over TCP.

---

### **Q3: What is the difference between Recursive and Iterative DNS resolution?**
**Answer:**  
- **Recursive Resolution:** The querying client delegates the entire resolution burden to a recursive resolver (e.g., ISP nameserver, Google `8.8.8.8`). The resolver contacts root servers, TLD servers, and authoritative servers on the client's behalf, returning the final answer or error.
- **Iterative Resolution:** The queried server does not perform further lookups. Instead, it returns the best referral it knows (the IP of the next nameserver down the tree). The client itself must contact each nameserver iteratively until reaching the authoritative source.

---

### **Q4: Why are there only 13 root server addresses (A through M), and how do they handle global traffic?**
**Answer:**  
Historical DNS packets over UDP were constrained to 512 bytes to avoid IPv4 fragmentation. To fit within a single UDP datagram with necessary protocol headers, only 13 root server IPv4 addresses could be accommodated (`a.root-servers.net` to `m.root-servers.net`).  
Today, each of these 13 IP addresses utilizes **IP Anycast** routing. There are over 1,500 physical server instances distributed across the globe sharing those 13 IP addresses. BGP routes queries to the topologically nearest physical instance.

---

### **Q5: What is Time-To-Live (TTL) in DNS? Who configures it?**
**Answer:**  
TTL is a 32-bit integer in a Resource Record that dictates the maximum number of seconds a resolver or client is allowed to cache that record before discarding it. It is configured by the **authoritative zone administrator**.  
- High TTL (e.g., 86,400s / 24 hours): Maximizes caching benefits and minimizes nameserver load, but slows down record updates.
- Low TTL (e.g., 60s): Enables rapid failover, CDN load balancing, and fast IP migrations, but increases lookup traffic.

---

### **Q6: How does your simulator implement the Cache Hit vs. Cache Miss logic?**
**Answer:**  
1. When a user requests a domain and record type, the resolver constructs a composite key: `(normalized_domain, record_type)`.
2. It queries `DNSCache.get(domain, record_type)`:
   - **Cache Hit:** If the entry exists and `current_time < expires_at` (remaining TTL > 0). The simulator delivers records directly from local memory in <1 ms, bypassing external network calls.
   - **Cache Miss:** If the entry does not exist or its TTL has expired (`current_time >= expires_at`). The simulator queries the upstream DNS server over the network via `dnspython`, stores the returned record with its authoritative/demo TTL, and delivers the result.

---

### **Q7: Why does your cache index entries by `(domain, record_type)` rather than just `domain`?**
**Answer:**  
A single domain name can hold multiple distinct record types simultaneously. For instance:
- `google.com` with type `A` yields IPv4 addresses.
- `google.com` with type `AAAA` yields IPv6 addresses.
- `google.com` with type `MX` yields mail exchange servers.
- `google.com` with type `TXT` yields verification strings.  
If we only indexed by domain, querying an MX record would overwrite or conflict with the cached A record. Composite indexing ensures complete record isolation.

---

### **Q8: What is the purpose of the Demo TTL Mode in your project?**
**Answer:**  
In production, authoritative TTLs are often 300 seconds (5 minutes) to 86,400 seconds (24 hours). During an oral examination or short presentation, waiting 5 minutes to verify cache expiration is impractical. The **Demo TTL Mode (10s, 30s, 60s)** overrides the stored TTL, allowing examiners to observe the live real-time countdown reach zero and witness the immediate transition to a Cache Miss within seconds.

---

### **Q9: Why are Cache Hits so much faster than Cache Misses?**
**Answer:**  
- **Cache Hit Latency ($\approx 0.1 \text{ ms}$):** Data resides in RAM. The operation is simply an in-memory hash table lookup with negligible microsecond-level CPU memory bus access.
- **Cache Miss Latency ($\approx 30 - 150 \text{ ms}$):** The request must serialize into a UDP packet, pass through the OS networking stack, traverse physical network cables/routers, cross ISP backbones to reach the DNS server (e.g. `8.8.8.8`), be resolved, and travel back. This round-trip propagation and transmission delay accounts for the latency difference (often a 300× speedup).

---

### **Q10: What is the difference between an `A` record and an `AAAA` record?**
**Answer:**  
- **`A` Record (Address Record):** Maps a hostname to a 32-bit **IPv4** address (e.g., `142.250.190.46`). Defined in RFC 1035.
- **`AAAA` Record (Quad-A Record):** Maps a hostname to a 128-bit **IPv6** address (e.g., `2607:f8b0:4005:805::200e`). Defined in RFC 3596. It is called "Quad-A" because 128 bits is four times the size of a 32-bit IPv4 address.

---

### **Q11: What is a `CNAME` record, and what is the CNAME restriction?**
**Answer:**  
A **CNAME (Canonical Name)** record creates an alias pointing one domain name to another canonical domain (e.g., `www.example.com` $\rightarrow$ `example.com`).  
**The CNAME Restriction:** According to RFC 1034, if a CNAME record exists for a name, no other record types (`A`, `MX`, `TXT`) can exist for that identical name. Consequently, a CNAME cannot be placed at the zone apex (`@` or root domain like `example.com`), which requires SOA and NS records.

---

### **Q12: What is an `MX` record and why does it have an integer preference/priority value?**
**Answer:**  
An **MX (Mail Exchange)** record specifies the mail server responsible for accepting incoming email on behalf of a domain.  
The preference value (e.g., `10 smtp.google.com`) is an unsigned 16-bit integer determining delivery priority:
- Senders must attempt delivery to the mail server with the **lowest numerical priority** first (primary server).
- If that server is unreachable, senders fall back to higher numerical values (backup/secondary mail servers).

---

### **Q13: What is a `TXT` record, and how is it used in email authentication?**
**Answer:**  
A `TXT` record holds human- or machine-readable text data. While originally intended for arbitrary notes, it is predominantly used today for cybersecurity authentication:
1. **SPF (Sender Policy Framework):** Declares which IP addresses are authorized to send emails on behalf of the domain (e.g., `v=spf1 include:_spf.google.com ~all`).
2. **DKIM (DomainKeys Identified Mail):** Publishes the domain's public cryptographic key used to verify digital signatures on outbound emails.
3. **DMARC:** Specifies policy actions (quarantine, reject) when SPF or DKIM validation fails.

---

### **Q14: What is an `NXDOMAIN` response?**
**Answer:**  
`NXDOMAIN` (Non-Existent Domain, RCODE 3) is a response code returned by an authoritative nameserver indicating that the requested domain name does not exist anywhere within the DNS namespace.

---

### **Q15: What is Negative Caching, and which RFC specifies it?**
**Answer:**  
Specified in **RFC 2308**, negative caching is the practice of caching failure responses (such as `NXDOMAIN` or `NODATA`). Without negative caching, a misconfigured application querying a non-existent domain would repeatedly hammer root/authoritative nameservers. The negative response is cached using the `MINIMUM` TTL field found in the zone's SOA (Start of Authority) record.

---

### **Q16: What is DNS Cache Poisoning (Kaminsky Attack)?**
**Answer:**  
DNS Cache Poisoning occurs when an attacker injects fraudulent DNS records into a caching resolver's memory, redirecting legitimate users to malicious IP addresses.  
In 2008, Dan Kaminsky discovered a flaw where attackers flooded recursive resolvers with spoofed UDP replies guessing the 16-bit **DNS Transaction ID (TxID)**.  
**Mitigation:**
1. **Source Port Randomization (SPR):** Randomizing both the 16-bit TxID and the 16-bit UDP source port creates $\approx 4 \text{ billion}$ combinations, making brute-force spoofing computationally infeasible.
2. **DNSSEC:** Cryptographically signing DNS zones.

---

### **Q17: What is DNSSEC and how does it protect DNS?**
**Answer:**  
**DNSSEC (Domain Name System Security Extensions)** adds cryptographic authentication and integrity verification to DNS responses without encrypting payloads:
- Authoritative servers sign Resource Record Sets using private keys to generate **RRSIG** records.
- Resolvers verify signatures using public keys stored in **DNSKEY** records.
- Trust is established through a cryptographic **Chain of Trust** anchored at the Root Zone (`.` trust anchor) down through **DS (Delegation Signer)** records in parent zones.

---

### **Q18: What are DoH (DNS over HTTPS) and DoT (DNS over TLS)?**
**Answer:**  
Standard DNS queries travel in plain text, allowing ISPs, governments, or eavesdroppers on public Wi-Fi to intercept or manipulate queries.
- **DoT (RFC 7858):** Wraps DNS queries directly in TLS over dedicated **Port 853**.
- **DoH (RFC 8484):** Transmits DNS queries as HTTP/2 or HTTP/3 binary payloads over HTTPS on standard **Port 443**, blending DNS queries indistinguishably into standard encrypted web traffic.

---

### **Q19: Why did you use `dnspython` instead of Python's built-in `socket.gethostbyname()`?**
**Answer:**  
`socket.gethostbyname()` only performs basic IPv4 A-record resolution using the underlying operating system's C library stub resolver. It has major limitations:
1. It does not provide access to record TTLs.
2. It does not support querying specific record types like `MX`, `TXT`, `AAAA`, `NS`, or `CNAME`.
3. It does not permit directing queries to custom nameservers (like `1.1.1.1` or `8.8.8.8`).  
`dnspython` is a full DNS protocol toolkit that constructs actual DNS wire-format packets, inspects RRsets, extracts authoritative TTLs, and handles raw DNS error codes.

---

### **Q20: Why was threading necessary in your GUI application?**
**Answer:**  
GUI frameworks like Tkinter run on a single main thread that manages event dispatching, widget rendering, and window responsiveness. When a DNS lookup encounters packet loss, slow nameservers, or timeouts, the network call can block for up to 4–5 seconds. If performed on the main thread, the OS marks the window as "Not Responding" and freezes animations. Spawning a detached worker thread keeps the UI smooth and responsive at 60 FPS while network lookups proceed in the background.

---

### **Q21: How is thread safety achieved in your `DNSCache` class?**
**Answer:**  
In Python, dictionary operations like insertion or deletion are not inherently guaranteed to be thread-safe across complex check-then-act logic. In our app, background worker threads write new entries while the GUI main thread continuously reads entries to render tables and tick down countdown timers.  
We wrapped all cache read/write operations using `threading.RLock()` (Re-entrant Mutual Exclusion Lock). This ensures atomic access and prevents race conditions or `RuntimeError: dictionary changed size during iteration`.

---

### **Q22: How is the Cache Hit Ratio calculated?**
**Answer:**  
The Cache Hit Ratio measures the percentage of total incoming DNS queries successfully satisfied by the local cache:
$$\text{Cache Hit Ratio} = \left( \frac{\text{Cache Hits}}{\text{Total Queries}} \right) \times 100$$
For example, if the application executes 10 queries, and 7 are resolved from local memory while 3 require network lookups, the Hit Ratio is:
$$\text{Hit Ratio} = \left( \frac{7}{10} \right) \times 100 = 70.0\%$$

---

### **Q23: How does the live TTL countdown work in the GUI without freezing?**
**Answer:**  
Instead of using a blocking `while True: time.sleep(1)` loop, the application uses Tkinter's non-blocking event-driven timer:
```python
self.root.after(1000, self._schedule_ttl_tick)
```
Every 1000 milliseconds, the event loop triggers `_tick_ttl()`, which re-calculates `remaining_ttl = max(0, int(expires_at - time.time()))` for active entries and updates the labels.

---

### **Q24: What happens if a domain's IP changes while it is still cached in your application?**
**Answer:**  
Until the cached entry's TTL reaches zero, the simulator will continue to return the cached IP address (Cache Hit). This represents standard DNS behavior: clients will not see the updated IP until the cached record expires. Once expired, the next query triggers a Cache Miss, contacting the upstream DNS server and retrieving the newly updated IP address.

---

### **Q25: What formats can query history be exported to in your project?**
**Answer:**  
The project implements export methods in `statistics.py` that serialize the complete query history and performance metrics to:
1. **CSV (Comma-Separated Values):** Structured spreadsheet format including columns for Index, Timestamp, Domain, Type, Hit/Miss Status, Latency (ms), Server, and Records.
2. **JSON (JavaScript Object Notation):** Hierarchical structure containing an aggregated statistical summary alongside arrayed query records, ideal for automated parsing or database ingestion.

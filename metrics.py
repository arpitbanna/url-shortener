from prometheus_client import Counter, Histogram, Gauge

# -------------------------------------------------------
# 🌐 HTTP Request Metrics (general API observability)
# -------------------------------------------------------

# Total number of HTTP requests, categorized by method, endpoint, and status code.
# Helps track traffic volume and API usage patterns.
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"]
)

# Distribution of HTTP request latency, measured in seconds.
# Useful for detecting performance issues and tracking response time SLAs.
REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["endpoint"]
)


# -------------------------------------------------------
# 🚨 Fraud / Suspicious Activity Metrics
# -------------------------------------------------------

# Total number of suspicious requests detected, grouped by detection type
# (e.g., "ip_rate", "user_agent", "referrer", "ip_url").
# Maps to suspicious_clicks table (reason column).
SUSPICIOUS_REQUESTS = Counter(
    "suspicious_requests_total", 
    "Total number of suspicious requests detected",
    ["type"]
)

# Current number of unique IPs flagged as suspicious (active cases).
# Derived from suspicious_clicks.ip field in the database.
SUSPICIOUS_IPS = Gauge(
    "suspicious_ips_current",
    "Number of currently suspicious IPs"
)

# Current number of URL-specific suspicious activities,
# showing how many unique IP+URL combinations were flagged.
SUSPICIOUS_IP_URLS = Gauge(
    "suspicious_ip_urls_current",
    "Number of currently suspicious IP+URL combinations"
)


# -------------------------------------------------------
# 📊 URL & Click Analytics (business KPIs)
# -------------------------------------------------------

# Tracks unique visitors per URL.
# Each visitor should be counted once, based on IP or fingerprint.
# Maps to url_clicks table (ip, fingerprint).
UNIQUE_VISITORS = Counter(
    "unique_visitors_total",
    "Number of unique visitors",
    ["url", "date"]
)

# Tracks how many clicks each URL received from each referrer domain.
# Maps to url_referrers table.
TOP_REFERRERS = Counter(
    "top_referrers",
    "Referrer counts",
    ["url", "referrer"]
)

# Distribution of the time gap between consecutive clicks on the same URL.
# Helps detect bots (low latency) vs. engaged users.
# Derived from url_clicks.clicked_at timestamps.
CLICK_LATENCY = Histogram(
    "click_latency_seconds",
    "Time between clicks",
    ["url"]
)

# Counts clicks flagged as suspicious or fraudulent.
# Label 'type' describes why it was flagged (e.g., "bot", "velocity", "ip_threshold").
# Maps to suspicious_clicks.reason column.
SUSPICIOUS_CLICKS = Counter(
    "suspicious_clicks_total",
    "Suspicious clicks detected",
    ["url", "type"]
)

# -------------------------------------------------------
# 🌍 Enriched Analytics: Geo & Device Insights
# -------------------------------------------------------

# Number of clicks per country for each URL.
# IP → Geo lookup populates this.
# Maps to url_clicks.ip + enrichment pipeline.
CLICKS_BY_COUNTRY = Counter(
    "clicks_by_country_total",
    "Number of clicks grouped by country",
    ["url", "country"]
)

# Number of clicks by device type (mobile, tablet, desktop).
# Parsed from User-Agent string.
CLICKS_BY_DEVICE = Counter(
    "clicks_by_device_total",
    "Clicks by device type (mobile, tablet, pc)",
    ["url", "device"]
)

# Number of clicks by browser family (Chrome, Firefox, Safari, etc.).
# Parsed from User-Agent string.
CLICKS_BY_BROWSER = Counter(
    "clicks_by_browser_total",
    "Clicks by browser",
    ["url", "browser"]
)

# Distribution of clicks over the 24 hours of the day.
# Useful for engagement timing and activity trends.
# Derived from url_clicks.clicked_at field.
CLICKS_BY_HOUR = Histogram(
    "clicks_by_hour",
    "Clicks by hour of day",
    ["url"]
)

from prometheus_client import Counter, Histogram,Gauge

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["endpoint"]
)

# Total number of suspicious requests
SUSPICIOUS_REQUESTS = Counter(
    'suspicious_requests_total', 
    'Total number of suspicious requests detected',
    ['type']  # e.g., "ip_rate", "user_agent", "referrer", "ip_url"
)

# Current number of IPs flagged as suspicious
SUSPICIOUS_IPS = Gauge(
    'suspicious_ips_current',
    'Number of currently suspicious IPs'
)

# Current number of URL-specific suspicious activity
SUSPICIOUS_IP_URLS = Gauge(
    'suspicious_ip_urls_current',
    'Number of currently suspicious IP+URL combinations'
)


from prometheus_client import Counter, Histogram

# Tracks the total number of unique visitors per URL.
# Each visitor should be counted once per URL, typically by fingerprint or IP.
UNIQUE_VISITORS = Counter(
    "unique_visitors", 
    "Number of unique visitors", 
    ["url"]
)

# Tracks how many clicks each URL received from each referrer.
# Useful to identify top referring sites or marketing sources.
TOP_REFERRERS = Counter(
    "top_referrers", 
    "Referrer counts", 
    ["url", "referrer"]
)

# Measures the time between consecutive clicks on the same URL.
# Helps detect rapid-fire clicks or bots, and analyze user engagement.
CLICK_LATENCY = Histogram(
    "click_latency_seconds", 
    "Time between clicks", 
    ["url"]
)

# Counts the number of clicks flagged as suspicious/fraudulent.
# Label 'type' describes why the click was suspicious (e.g., bot, velocity, IP threshold).
SUSPICIOUS_CLICKS = Counter(
    "suspicious_clicks_total", 
    "Suspicious clicks detected", 
    ["url", "type"]
)

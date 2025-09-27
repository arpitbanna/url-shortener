-- =====================================
-- Users Table
-- =====================================
CREATE TABLE IF NOT EXISTS users (
    id CHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_username ON users(username);

-- =====================================
-- URLs Table
-- =====================================
CREATE TABLE IF NOT EXISTS urls (
    id CHAR(36) PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    original_url TEXT NOT NULL,
    user_id CHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    clicks INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_code ON urls(code);
CREATE INDEX idx_user_id ON urls(user_id);
CREATE INDEX idx_urls_user_id_created_at ON urls(user_id, created_at);
CREATE INDEX idx_urls_code_user_id ON urls(code, user_id);
CREATE INDEX idx_urls_created_at ON urls(created_at);

-- =====================================
-- URL Clicks Table
-- =====================================
CREATE TABLE IF NOT EXISTS url_clicks (
    id CHAR(36) PRIMARY KEY,
    url_id CHAR(36) NOT NULL,
    fingerprint CHAR(64),
    ip VARCHAR(45),
    user_agent TEXT,
    referrer TEXT,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (url_id) REFERENCES urls(id) ON DELETE CASCADE
);

CREATE INDEX idx_url_clicks_url_id_clicked_at ON url_clicks(url_id, clicked_at);
CREATE INDEX idx_url_clicks_ip ON url_clicks(ip);
CREATE INDEX idx_url_clicks_user_agent ON url_clicks(user_agent(50));
CREATE INDEX idx_url_clicks_referrer ON url_clicks(referrer(50));
CREATE INDEX idx_url_clicks_clicked_at ON url_clicks(clicked_at);
CREATE INDEX idx_clicks_fingerprint ON url_clicks(fingerprint);

-- =====================================
-- Suspicious Clicks Table
-- =====================================
CREATE TABLE IF NOT EXISTS suspicious_clicks (
    id CHAR(36) PRIMARY KEY,
    fingerprint CHAR(64),
    ip VARCHAR(45),
    user_agent TEXT,
    referrer TEXT,
    reason TEXT,
    url_code VARCHAR(10),
    metadata TEXT
);

-- =====================================
-- Hourly Analytics Table
-- =====================================
CREATE TABLE IF NOT EXISTS url_analytics_hourly (
    url_id CHAR(36),
    date_hour DATETIME NOT NULL, -- truncated to hour
    clicks INT DEFAULT 0,
    unique_visitors INT DEFAULT 0,
    suspicious_clicks INT DEFAULT 0,
    PRIMARY KEY(url_id, date_hour)
);

CREATE INDEX idx_analytics_url_hour ON url_analytics_hourly(url_id, date_hour);

-- =====================================
-- User Sequences Table (Behavioral)
-- =====================================
CREATE TABLE IF NOT EXISTS user_sequences (
    fingerprint CHAR(64) PRIMARY KEY,
    sequence JSON, -- last N URL codes
    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_sequences_last_update ON user_sequences(last_update);

-- =====================================
-- URL Referrers Table
-- =====================================
CREATE TABLE IF NOT EXISTS url_referrers (
    url_id CHAR(36),
    referrer TEXT,
    clicks INT DEFAULT 0,
    PRIMARY KEY(url_id, referrer)
);

CREATE INDEX idx_referrers_url ON url_referrers(url_id);
CREATE INDEX idx_referrers_clicks ON url_referrers(url_id, clicks DESC);

-- =====================================
-- User Statistics Table
-- =====================================
CREATE TABLE IF NOT EXISTS user_statistics (
    user_id CHAR(36),
    fingerprint CHAR(64),
    total_urls INT DEFAULT 0,
    total_clicks INT DEFAULT 0,
    suspicious_clicks INT DEFAULT 0,
    PRIMARY KEY(user_id, fingerprint)
);

CREATE INDEX idx_user_statistics ON user_statistics(fingerprint);

-- =====================================
-- Additional Indexes
-- =====================================
-- Ensures fast querying for click rate per IP or URL
CREATE INDEX idx_url_clicks_url_ip ON url_clicks(url_id, ip);
CREATE INDEX idx_url_clicks_url_user_agent ON url_clicks(url_id, user_agent(50));


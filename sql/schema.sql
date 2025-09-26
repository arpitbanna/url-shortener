CREATE TABLE IF NOT EXISTS users (
    id CHAR(36) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    user_role ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS urls (
    id CHAR(36) PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    -- short code, e.g., 'abc123'
    original_url TEXT NOT NULL,
    -- the full original URL
    user_id CHAR(36) NOT NULL,
    -- owner of the URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS url_clicks (
    id CHAR(36) PRIMARY KEY,
    url_id CHAR(36) NOT NULL,
    ip VARCHAR(45),
    user_agent TEXT,
    referrer TEXT,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (url_id) REFERENCES urls(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_code ON urls(code);
CREATE INDEX idx_user_id ON urls(user_id);
CREATE INDEX idx_url_clicks_id ON url_clicks(url_id);
CREATE INDEX idx_url_clicks_urlid_clickedat ON url_clicks(url_id, clicked_at);
ALTER TABLE urls ADD COLUMN clicks INT DEFAULT 0;

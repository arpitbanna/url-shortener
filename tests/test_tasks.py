# tests/test_tasks.py
import pytest
from unittest.mock import MagicMock
from tasks import log_click, check_fraud, update_trending_urls

# ----------------------------
# Test log_click
# ----------------------------
def test_log_click_runs_without_error(mocker):
    # Mock DB connection
    mock_conn = mocker.patch("tasks.get_connection")
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value = mock_cursor

    # Mock Redis
    mocker.patch("tasks.redis_client")

    # Mock metrics
    mock_metrics = mocker.patch("tasks.UNIQUE_VISITORS")
    mocker.patch("tasks.TOP_REFERRERS")
    mocker.patch("tasks.CLICKS_BY_COUNTRY")
    mocker.patch("tasks.CLICKS_BY_DEVICE")
    mocker.patch("tasks.CLICKS_BY_BROWSER")
    mocker.patch("tasks.CLICKS_BY_HOUR")

    # Mock analytics functions
    mocker.patch("tasks.increment_hourly_analytics")
    mocker.patch("tasks.update_user_sequence")
    mocker.patch("tasks.update_url_referres")

    # Mock helpers
    mocker.patch("tasks.get_country_from_ip", return_value="us")
    mocker.patch("tasks.parse_user_agent", return_value=("pc", "chrome"))
    mocker.patch("uuid.uuid4", return_value="test-uuid")

    # Run task
    result = log_click(
        url_id="url123",
        ip="1.2.3.4",
        user_agent="Mozilla/5.0",
        referrer="https://ref.com",
        fingerprint="fp123"
    )  # type: ignore

    assert result is None
    assert mock_cursor.execute.called
    mock_metrics.labels().inc.assert_called()

# ----------------------------
# Test check_fraud
# ----------------------------
def test_check_fraud_detects_suspicious(mocker):
    # Mock heuristic functions
    mocker.patch("tasks.is_fraud", return_value=True)
    mocker.patch("tasks.check_velocity", return_value=False)
    mocker.patch("tasks.check_behavior", return_value=False)

    # Mock DB & analytics
    mock_conn = mocker.patch("tasks.get_connection")
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value = mock_cursor
    mocker.patch("tasks.increment_hourly_analytics")

    # Mock metrics
    mocker.patch("tasks.SUSPICIOUS_REQUESTS")
    mocker.patch("tasks.SUSPICIOUS_CLICKS")
    mocker.patch("tasks.SUSPICIOUS_IPS")
    mocker.patch("tasks.SUSPICIOUS_IP_URLS")
    mocker.patch("uuid.uuid4", return_value="test-uuid")

    suspicious = check_fraud(
        ip="1.2.3.4",
        url_id="url123",
        user_agent="Mozilla/5.0",
        referrer="https://ref.com",
        fingerprint="fp123"
    )  # type: ignore

    assert suspicious is True
    assert mock_cursor.execute.called

# ----------------------------
# Test update_trending_urls
# ----------------------------
def test_update_trending_urls(mocker):
    # Mock DB
    mock_conn = mocker.patch("tasks.get_connection")
    mock_cursor = MagicMock()
    mock_conn.return_value.cursor.return_value = mock_cursor
    # Mock fetchall result
    mock_cursor.fetchall.return_value = [
        {"url_id": "url123", "trending_score": 10.0},
        {"url_id": "url456", "trending_score": 5.0},
    ]

    # Mock Redis
    mock_redis = mocker.patch("tasks.redis_client")

    # Run task
    update_trending_urls(top_n=2)

    assert mock_cursor.execute.called
    mock_redis.set.assert_called()

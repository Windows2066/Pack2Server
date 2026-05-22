from datetime import UTC, datetime, timedelta

from app.services.cleanup import is_expired


def test_is_expired_returns_true_after_expiry():
    assert is_expired(datetime.now(UTC) - timedelta(seconds=1))


def test_is_expired_returns_false_before_expiry():
    assert not is_expired(datetime.now(UTC) + timedelta(hours=1))

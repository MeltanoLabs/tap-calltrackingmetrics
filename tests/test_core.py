"""Tests standard tap features using the built-in SDK tests library."""

import zoneinfo
from datetime import datetime, timezone

from singer_sdk.testing import get_tap_test_class

from tap_calltrackingmetrics.streams import is_utc, start_date_from_bookmark
from tap_calltrackingmetrics.tap import TapCallTrackingMetrics

TestCallTrackingMetrics = get_tap_test_class(
    TapCallTrackingMetrics,
    include_tap_tests=False,
    include_stream_tests=False,
    include_stream_attribute_tests=False,
)


def test_is_utc() -> None:
    naive = datetime(2024, 1, 1)  # noqa: DTZ001
    eastern_dt = datetime(2024, 1, 1, tzinfo=zoneinfo.ZoneInfo("America/New_York"))
    utc_dt = datetime(2024, 1, 1, tzinfo=timezone.utc)

    assert is_utc(naive) is False
    assert is_utc(eastern_dt) is False
    assert is_utc(utc_dt) is True


def test_start_date_from_bookmark() -> None:
    # Naive strings stay on the same day
    assert start_date_from_bookmark("2024-01-15") == "2024-01-15"
    assert start_date_from_bookmark("2024-01-15T02:00:00") == "2024-01-15"

    # Early UTC is rolled back to the previous day to prevent data loss
    early_utc = datetime(2024, 1, 15, 2, tzinfo=timezone.utc)
    assert early_utc.isoformat() == "2024-01-15T02:00:00+00:00"
    assert start_date_from_bookmark(early_utc.isoformat()) == "2024-01-14"
    assert start_date_from_bookmark(early_utc.timestamp()) == "2024-01-14"

    # Not-so-early UTC stays within the same day
    not_so_early_utc = datetime(2024, 1, 15, 14, tzinfo=timezone.utc)
    assert not_so_early_utc.isoformat() == "2024-01-15T14:00:00+00:00"
    assert start_date_from_bookmark(not_so_early_utc.isoformat()) == "2024-01-15"
    assert start_date_from_bookmark(not_so_early_utc.timestamp()) == "2024-01-15"

    assert start_date_from_bookmark(None) is None

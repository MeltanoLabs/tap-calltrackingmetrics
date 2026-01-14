"""Tests standard tap features using the built-in SDK tests library."""

from singer_sdk.testing import get_tap_test_class

from tap_calltrackingmetrics.streams import start_date_from_bookmark
from tap_calltrackingmetrics.tap import TapCallTrackingMetrics

TestCallTrackingMetrics = get_tap_test_class(
    TapCallTrackingMetrics,
    include_tap_tests=False,
    include_stream_tests=False,
    include_stream_attribute_tests=False,
)


def test_start_date_from_bookmark() -> None:
    assert start_date_from_bookmark("2024-01-01") == "2024-01-01"
    assert start_date_from_bookmark(1704088800) == "2024-01-01"
    assert start_date_from_bookmark(None) is None

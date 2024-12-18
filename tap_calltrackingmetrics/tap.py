"""CallTrackingMetrics tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_calltrackingmetrics import streams


class TapCallTrackingMetrics(Tap):
    """CallTrackingMetrics tap class."""

    name = "tap-calltrackingmetrics"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "access_key",
            th.StringType,
            required=True,
            title="Access Key",
            description="Access Key from the CallTrackingMetrics UI.",
        ),
        th.Property(
            "secret_key",
            th.StringType,
            required=True,
            secret=True,
            title="Secret Key",
            description="Secret Key from the CallTrackingMetrics UI.",
        ),
        th.Property(
            "start_date",
            th.DateTimeType,
            required=False,
            title="Start Date",
            description="The earliest record to sync.",
        ),
    ).to_dict()

    def discover_streams(self) -> list[streams.CallTrackingMetricsStream]:
        """Return a list of discovered streams.

        Returns:
            A list of discovered streams.
        """
        return [
            streams.AccountStream(self),
            streams.UserStream(self),
            streams.CallStream(self),
            streams.SaleStream(self),
            streams.ContactListStream(self),
            streams.ContactListDetailStream(self),
            streams.TriggerStream(self),
        ]


if __name__ == "__main__":
    TapCallTrackingMetrics.cli()

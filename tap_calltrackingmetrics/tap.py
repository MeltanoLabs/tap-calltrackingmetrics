"""CallTrackingMetrics tap class."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from singer_sdk import Tap
from singer_sdk import typing as th  # JSON schema typing helpers

from tap_calltrackingmetrics import streams

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from singer_sdk import Stream


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

    @override
    def discover_streams(self) -> list[Stream]:
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

"""Stream type classes for tap-calltrackingmetrics."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from singer_sdk import SchemaDirectory, StreamSchema

from tap_calltrackingmetrics import schemas
from tap_calltrackingmetrics.client import (
    CallTrackingMetricsStream,
    PaginatedCallTrackingMetricsStream,
)

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from singer_sdk.helpers.types import Context, Record


SCHEMAS_DIR = SchemaDirectory(schemas)


def is_utc(dt: datetime) -> bool:
    """Check if a datetime is timezone-aware AND in UTC."""
    return dt.tzinfo is not None and (offset := dt.tzinfo.utcoffset(dt)) is not None and offset.total_seconds() == 0


def start_date_from_bookmark(bookmark: str | float | None) -> str | None:
    if bookmark is None:
        return None

    if isinstance(bookmark, str):
        dt = datetime.fromisoformat(bookmark)

    elif isinstance(bookmark, (int, float)):
        dt = datetime.fromtimestamp(bookmark, tz=timezone.utc)

    # For UTC hours between 00:00 and 8:59, subtract 9 hours to avoid gaps caused by
    # the CTM API interpreting start_date as midnight in its local US timezone (up to UTC-8),
    # while our bookmark is in UTC. Without this buffer, calls in the early UTC hours of the
    # bookmark date would never be fetched.
    if is_utc(dt) and dt.hour < 9:  # noqa: PLR2004
        dt -= timedelta(hours=9)

    return dt.strftime("%Y-%m-%d")


class AccountStream(PaginatedCallTrackingMetricsStream):
    name = "account"
    path = "/api/v1/accounts"
    records_jsonpath = "$.accounts[*]"
    primary_keys = ("id",)
    replication_key = None
    schema = StreamSchema(SCHEMAS_DIR)

    @override
    def get_child_context(self, record: Record, context: Context | None) -> Context | None:
        return {
            "_sdc_account_id": record["id"],
        }


class UserStream(PaginatedCallTrackingMetricsStream):
    name = "user"
    path = "/api/v1/accounts/{_sdc_account_id}/users"
    records_jsonpath = "$.users[*]"
    primary_keys = ("id",)
    replication_key = None
    schema = StreamSchema(SCHEMAS_DIR)
    parent_stream_type = AccountStream


class CallStream(PaginatedCallTrackingMetricsStream):
    name = "call"
    path = "/api/v1/accounts/{_sdc_account_id}/calls"
    records_jsonpath = "$.calls[*]"
    primary_keys = ("id",)
    replication_key = "unix_time"
    schema = StreamSchema(SCHEMAS_DIR)
    parent_stream_type = AccountStream

    @override
    def get_url_params(self, context: Context | None, next_page_token: str | None) -> dict[str, Any]:
        params = super().get_url_params(context, next_page_token)
        value = self.get_starting_replication_key_value(context)
        if start_date := start_date_from_bookmark(value):
            params["start_date"] = start_date
        return params

    @override
    def get_child_context(self, record: Record, context: Context | None) -> Context | None:
        assert context, "Context is expected here"  # noqa: S101
        return {
            "_sdc_account_id": context["_sdc_account_id"],
            "_sdc_call_id": record["id"],
        }


class SaleStream(CallTrackingMetricsStream):
    name = "sale"
    path = "/api/v1/accounts/{_sdc_account_id}/calls/{_sdc_call_id}/sale"
    records_jsonpath = "$"
    primary_keys = ("_sdc_account_id", "_sdc_call_id")
    replication_key = None
    schema = StreamSchema(SCHEMAS_DIR)
    parent_stream_type = CallStream


class TriggerStream(PaginatedCallTrackingMetricsStream):
    name = "trigger"
    path = "/api/v1/accounts/{_sdc_account_id}/triggers"
    records_jsonpath = "$.automators[*]"
    primary_keys = ("id",)
    replication_key = None
    schema = StreamSchema(SCHEMAS_DIR)
    parent_stream_type = AccountStream


class ContactListStream(PaginatedCallTrackingMetricsStream):
    # Maximum page size is 10, using higher numbers causes results to be truncated
    PAGE_SIZE = 10

    name = "contact_list"
    path = "/api/v1/accounts/{_sdc_account_id}/lists"
    records_jsonpath = "$.contact_lists[*]"
    primary_keys = ("id",)
    replication_key = None
    schema = StreamSchema(SCHEMAS_DIR)
    parent_stream_type = AccountStream

    @override
    def get_child_context(self, record: Record, context: Context | None) -> Context | None:
        assert context, "Context is expected here"  # noqa: S101
        return {
            "_sdc_account_id": context["_sdc_account_id"],
            "_sdc_contact_list_id": record["id"],
        }


class ContactListDetailStream(PaginatedCallTrackingMetricsStream):
    # Maximum page size is 10, using higher numbers causes results to be truncated
    PAGE_SIZE = 10

    name = "contact_list_detail"
    path = "/api/v1/accounts/{_sdc_account_id}/lists/{_sdc_contact_list_id}/contacts"
    records_jsonpath = "$.contacts[*]"
    primary_keys = ("id",)
    replication_key = None
    schema = StreamSchema(SCHEMAS_DIR)
    parent_stream_type = ContactListStream

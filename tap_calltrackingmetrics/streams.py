"""Stream type classes for tap-calltrackingmetrics."""

from __future__ import annotations

import datetime
import typing as t
from importlib import resources

from tap_calltrackingmetrics.client import (
    CallTrackingMetricsStream,
    PaginatedCallTrackingMetricsStream,
)

if t.TYPE_CHECKING:
    from singer_sdk.helpers import types


SCHEMAS_DIR = resources.files(__package__) / "schemas"


class AccountStream(PaginatedCallTrackingMetricsStream):

    name = "account"
    path = "/api/v1/accounts"
    records_jsonpath = "$.accounts[*]"
    primary_keys: t.ClassVar[list[str]] = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "account.json"

    def get_child_context(
        self,
        record: types.Record,
        context: types.Context | None,  # noqa: ARG002
    ) -> types.Context | None:
        return {
            "_sdc_account_id": record["id"],
        }


class UserStream(PaginatedCallTrackingMetricsStream):

    name = "user"
    path = "/api/v1/accounts/{_sdc_account_id}/users"
    records_jsonpath = "$.users[*]"
    primary_keys: t.ClassVar[list[str]] = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "user.json"
    parent_stream_type = AccountStream


class CallStream(PaginatedCallTrackingMetricsStream):

    name = "call"
    path = "/api/v1/accounts/{_sdc_account_id}/calls"
    records_jsonpath = "$.calls[*]"
    primary_keys: t.ClassVar[list[str]] = ["id"]
    replication_key = "unix_time"
    schema_filepath = SCHEMAS_DIR / "call.json"
    parent_stream_type = AccountStream

    def get_url_params(
        self,
        context: types.Context | None,
        next_page_token: t.Any | None,
    ) -> dict[str, t.Any]:
        params = super().get_url_params(context, next_page_token)
        starting_replication_key_value = self.get_starting_replication_key_value(
            context
        ) or self.config.get("start_date")
        if "start_date" not in params and starting_replication_key_value is not None:
            start_date = datetime.datetime.fromtimestamp(
                starting_replication_key_value, tz=datetime.timezone.utc
            ).strftime("%Y-%m-%d")
            params["start_date"] = start_date
        return params

    def get_child_context(
        self,
        record: types.Record,
        context: types.Context | None,
    ) -> types.Context | None:
        return {
            "_sdc_account_id": context["_sdc_account_id"],
            "_sdc_call_id": record["id"],
        }


class SaleStream(CallTrackingMetricsStream):

    name = "sale"
    path = "/api/v1/accounts/{_sdc_account_id}/calls/{_sdc_call_id}/sale"
    records_jsonpath = "$"
    primary_keys: t.ClassVar[list[str]] = ["_sdc_account_id", "_sdc_call_id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "sale.json"
    parent_stream_type = CallStream

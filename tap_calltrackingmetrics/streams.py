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
    replication_key = "_sdc_timestamp"
    schema_filepath = SCHEMAS_DIR / "call.json"
    parent_stream_type = AccountStream

    def get_url_params(
        self,
        context: types.Context | None,
        next_page_token: t.Any | None,
    ) -> dict[str, t.Any]:
        params = super().get_url_params(context, next_page_token)
        starting_timestamp = self.get_starting_timestamp(context)
        if starting_timestamp is not None:
            params["start_date"] = starting_timestamp.strftime("%Y-%m-%d")
        return params

    def post_process(self, row: types.Record, context: types.Context | None) -> types.Record:
        row = super().post_process(row, context)
        row["_sdc_timestamp"] = datetime.datetime.fromtimestamp(
            row["unix_time"], tz=datetime.timezone.utc
        ).isoformat()
        return row

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


class TriggerStream(PaginatedCallTrackingMetricsStream):

    name = "trigger"
    path = "/api/v1/accounts/{_sdc_account_id}/triggers"
    records_jsonpath = "$.automators[*]"
    primary_keys: t.ClassVar[list[str]] = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "trigger.json"
    parent_stream_type = AccountStream


class ContactListStream(PaginatedCallTrackingMetricsStream):

    # Maximum page size is 10, using higher numbers causes results to be truncated
    PAGE_SIZE=10

    name = "contact_list"
    path = "/api/v1/accounts/{_sdc_account_id}/lists"
    records_jsonpath = "$.contact_lists[*]"
    primary_keys: t.ClassVar[list[str]] = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "contact_list.json"
    parent_stream_type = AccountStream

    def get_child_context(
        self,
        record: types.Record,
        context: types.Context | None,
    ) -> types.Context | None:
        return {
            "_sdc_account_id": context["_sdc_account_id"],
            "_sdc_contact_list_id": record["id"],
        }


class ContactListDetailStream(PaginatedCallTrackingMetricsStream):

    # Maximum page size is 10, using higher numbers causes results to be truncated
    PAGE_SIZE=10

    name = "contact_list_detail"
    path = "/api/v1/accounts/{_sdc_account_id}/lists/{_sdc_contact_list_id}/contacts"
    records_jsonpath = "$.contacts[*]"
    primary_keys: t.ClassVar[list[str]] = ["id"]
    replication_key = None
    schema_filepath = SCHEMAS_DIR / "contact_list_detail.json"
    parent_stream_type = ContactListStream

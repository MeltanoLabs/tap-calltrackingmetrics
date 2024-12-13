"""REST client handling, including CallTrackingMetricsStream base class."""

from __future__ import annotations

import typing as t
from importlib import resources
from urllib.parse import parse_qs, urlparse

from requests.auth import HTTPBasicAuth
from singer_sdk.helpers.jsonpath import extract_jsonpath
from singer_sdk.pagination import JSONPathPaginator
from singer_sdk.streams import RESTStream

if t.TYPE_CHECKING:
    import requests
    from singer_sdk.helpers.types import Context


SCHEMAS_DIR = resources.files(__package__) / "schemas"


class CallTrackingMetricsPaginator(JSONPathPaginator):

    def get_next(self, response: requests.Response) -> str | None:
        all_matches = extract_jsonpath(self._jsonpath, response.json())
        return next(all_matches, None)


class CallTrackingMetricsStream(RESTStream):
    """CallTrackingMetrics stream class."""

    url_base = "https://api.calltrackingmetrics.com"

    @property
    def authenticator(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(
            username=self.config.get("access_key", ""),
            password=self.config.get("secret_key", ""),
        )

    @property
    def http_headers(self) -> dict:
        return {}


class PaginatedCallTrackingMetricsStream(CallTrackingMetricsStream):

    # Going above a page size of 150 causes http 400 with response body:
    # {
    #     "error": "per_page limit is 150"
    # }
    PAGE_SIZE = 150

    next_page_token_jsonpath = "$.next_page"  # noqa: S105

    def get_new_paginator(self) -> CallTrackingMetricsPaginator:
        return CallTrackingMetricsPaginator(self.next_page_token_jsonpath)

    def get_url_params(
        self,
        context: Context | None,  # noqa: ARG002
        next_page_token: t.Any | None,
    ) -> dict[str, t.Any]:
        params: dict = {}
        params["per_page"] = self.PAGE_SIZE
        if next_page_token:
            for k, v in parse_qs(urlparse(next_page_token).query).items():
                params[k] = v[0]
        return params

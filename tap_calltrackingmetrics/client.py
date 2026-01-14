"""REST client handling, including CallTrackingMetricsStream base class."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse

from requests.auth import HTTPBasicAuth
from singer_sdk.streams import RESTStream

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from singer_sdk.helpers.types import Context


class CallTrackingMetricsStream(RESTStream[str]):
    """CallTrackingMetrics stream class."""

    url_base = "https://api.calltrackingmetrics.com"

    @override
    @property
    def authenticator(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(username=self.config["access_key"], password=self.config["secret_key"])


class PaginatedCallTrackingMetricsStream(CallTrackingMetricsStream):
    # Going above a page size of 150 causes http 400 with response body:
    # {
    #     "error": "per_page limit is 150"
    # }
    PAGE_SIZE = 150

    next_page_token_jsonpath = "$.next_page"  # noqa: S105

    @override
    def get_url_params(self, context: Context | None, next_page_token: str | None) -> dict[str, Any]:
        params: dict[str, Any] = {"per_page": self.PAGE_SIZE}
        if next_page_token:
            for k, v in parse_qs(urlparse(next_page_token).query).items():
                params[k] = v[0]
        return params

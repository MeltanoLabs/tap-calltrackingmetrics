from __future__ import annotations  # noqa: INP001

import json
import os
import sys
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from dotenv import load_dotenv
from genson import SchemaBuilder

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: PTH100, PTH120

from tap_calltrackingmetrics import streams
from tap_calltrackingmetrics.tap import TapCallTrackingMetrics

if TYPE_CHECKING:
    from singer_sdk import RESTStream
    from singer_sdk.helpers.types import Context

MAX_RECORDS = 1000  # maximum records to sync before generating a schema


def make_nullable(schema: dict[str, Any]) -> dict[str, Any]:
    """Make all properties in the schema nullable and remove 'required'."""
    if isinstance(schema, dict):
        if "type" in schema:
            if isinstance(schema["type"], str):
                schema["type"] = [schema["type"], "null"]
            elif isinstance(schema["type"], list) and "null" not in schema["type"]:
                schema["type"].append("null")

        # Remove 'required' key if it exists
        schema.pop("required", None)

        for value in schema.values():
            make_nullable(value)

        if "properties" in schema:
            for prop in schema["properties"].values():
                make_nullable(prop)

    return schema


def generate_schema(
    stream_instance: RESTStream[Any],
    context_list: list[Context],
    output_file: str,
) -> None:
    builder = SchemaBuilder()
    records: list[dict[str, Any]] = []
    for context in context_list:
        records.extend(stream_instance.get_records(context=context))

    def convert_decimal(obj: Any) -> float | dict[str, Any] | list[Any]:
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, dict):
            return {k: convert_decimal(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert_decimal(item) for item in obj]
        return obj

    # Process all records, up to 10,000
    for idx, item in enumerate(records):
        if idx >= MAX_RECORDS:
            break
        converted_item = convert_decimal(item)
        builder.add_object(converted_item)

    schema = builder.to_schema()  # Get the schema from builder
    schema = make_nullable(schema)  # Make all fields nullable

    if output_file is not None:
        with open(output_file, "w") as f:
            json.dump(schema, f, indent=2)


def main() -> None:
    # Load environment variables from .env file
    load_dotenv()

    config = {
        "access_key": os.getenv("TAP_CALLTRACKINGMETRICS_ACCESS_KEY"),
        "secret_key": os.getenv("TAP_CALLTRACKINGMETRICS_SECRET_KEY"),
    }

    tap = TapCallTrackingMetrics(config=config)

    # Configure this part as-needed for the streams you want to generate schemas for.
    grandparent = streams.AccountStream(tap=tap)
    parent = streams.CallStream(tap=tap)
    children = [streams.SaleStream(tap=tap)]

    gen = iter(grandparent.get_records(context=None))
    first = next(gen, None)
    if not first:
        msg = "no grandparent entries found"
        raise RuntimeError(msg)
    context = grandparent.get_child_context(record=first, context=None)

    context_list = []
    for parent_record in parent.get_records(context=context):
        if context := parent.get_child_context(record=parent_record, context=context):
            context_list.append(context)
        if len(context_list) >= MAX_RECORDS:
            for child in children:
                generate_schema(
                    child,
                    context_list=context_list,
                    output_file=f"tap_calltrackingmetrics/schemas/{child.name}.json",
                )
            break


if __name__ == "__main__":
    main()

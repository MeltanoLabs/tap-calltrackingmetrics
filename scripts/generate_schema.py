import json  # noqa: INP001
import os
import sys
import typing
from decimal import Decimal

from dotenv import load_dotenv
from genson import SchemaBuilder
from singer_sdk import RESTStream

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # noqa: PTH100, PTH120

from tap_calltrackingmetrics import streams
from tap_calltrackingmetrics.tap import TapCallTrackingMetrics

MAX_RECORDS = 1000  # maximum records to sync before generating a schema


def make_nullable(schema: dict) -> dict:
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
    stream_instance: RESTStream, context_list: list[dict], output_file: str
) -> None:
    builder = SchemaBuilder()
    records = []
    for context in context_list:
        records.extend(stream_instance.get_records(context=context))

    def convert_decimal(obj: typing.Any) -> float:
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

    gen = grandparent.get_records(context=None)
    first = next(gen, None)
    if not first:
        msg = "no grandparent entries found"
        raise RuntimeError(msg)
    context = grandparent.get_child_context(record=first, context=None)

    gen = parent.get_records(context=context)

    context_list = []
    for parent_record in gen:
        context_list.append(
            parent.get_child_context(record=parent_record, context=context)
        )
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

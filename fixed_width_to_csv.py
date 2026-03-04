#!/usr/bin/env python3
"""Convert fixed-width data to CSV using explicit input/output schemas in JSON config."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

Schema = List[Dict[str, Any]]
Context = Dict[str, str]


def load_config(config_path: Path) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    validate_config(config)
    return config


def validate_fixed_width_schema(schema: Any, context: str) -> None:
    if not isinstance(schema, list) or not schema:
        raise ValueError(f"'{context}' must be a non-empty list")

    names = set()
    for idx, column in enumerate(schema, start=1):
        if not isinstance(column, dict):
            raise ValueError(f"{context} entry #{idx} must be an object")
        if "name" not in column or "width" not in column:
            raise ValueError(f"{context} entry #{idx} must include 'name' and 'width'")
        if not isinstance(column["name"], str) or not column["name"].strip():
            raise ValueError(f"{context} entry #{idx} has invalid 'name'")
        if column["name"] in names:
            raise ValueError(f"Duplicate column name '{column['name']}' in {context}")
        names.add(column["name"])
        if not isinstance(column["width"], int) or column["width"] <= 0:
            raise ValueError(f"{context} entry #{idx} has invalid 'width' (must be > 0)")


def validate_output_schema(output_schema: Any) -> None:
    if not isinstance(output_schema, list) or not output_schema:
        raise ValueError("'output_schema' must be a non-empty list")

    seen = set()
    for idx, column in enumerate(output_schema, start=1):
        if not isinstance(column, dict):
            raise ValueError(f"output_schema entry #{idx} must be an object")
        if "name" not in column or "source" not in column:
            raise ValueError(f"output_schema entry #{idx} must include 'name' and 'source'")
        if not isinstance(column["name"], str) or not column["name"].strip():
            raise ValueError(f"output_schema entry #{idx} has invalid 'name'")
        if column["name"] in seen:
            raise ValueError(f"Duplicate output column name '{column['name']}'")
        seen.add(column["name"])
        if not isinstance(column["source"], str) or "." not in column["source"]:
            raise ValueError(
                f"output_schema entry #{idx} has invalid source '{column['source']}' (expected 'data.<field>' or 'header.<field>')"
            )


def validate_source_references(config: Dict[str, Any]) -> None:
    input_schema = config["input_schema"]
    data_fields = {c["name"] for c in input_schema["data_line"]}
    header_fields = {
        c["name"]
        for schema in input_schema.get("header_lines", [])
        for c in schema
    }

    for idx, output_col in enumerate(config["output_schema"], start=1):
        source = output_col["source"]
        source_type, field = source.split(".", 1)
        if source_type == "data":
            if field not in data_fields:
                raise ValueError(
                    f"output_schema entry #{idx} references unknown data field '{field}'"
                )
        elif source_type == "header":
            if field not in header_fields:
                raise ValueError(
                    f"output_schema entry #{idx} references unknown header field '{field}'"
                )
        else:
            raise ValueError(
                f"output_schema entry #{idx} has unsupported source prefix '{source_type}'"
            )


def validate_config(config: Dict[str, Any]) -> None:
    required_top_level = ["input_file", "output_file", "input_schema", "output_schema"]
    missing = [k for k in required_top_level if k not in config]
    if missing:
        raise ValueError(f"Missing required config keys: {', '.join(missing)}")

    input_schema = config["input_schema"]
    if not isinstance(input_schema, dict):
        raise ValueError("'input_schema' must be an object")
    if "data_line" not in input_schema:
        raise ValueError("'input_schema.data_line' is required")

    validate_fixed_width_schema(input_schema["data_line"], "input_schema.data_line")

    header_lines = input_schema.get("header_lines", [])
    if not isinstance(header_lines, list):
        raise ValueError("'input_schema.header_lines' must be a list when provided")
    for i, header_schema in enumerate(header_lines, start=1):
        validate_fixed_width_schema(header_schema, f"input_schema.header_lines[{i}]")

    validate_output_schema(config["output_schema"])
    validate_source_references(config)


def parse_fixed_width_line(line: str, schema: Schema, strip_values: bool) -> Context:
    cursor = 0
    values: Context = {}
    for column in schema:
        width = column["width"]
        raw = line[cursor : cursor + width]
        value = raw.strip() if strip_values else raw
        values[column["name"]] = value
        cursor += width
    return values


def parse_header_context(input_file: Path, header_schemas: List[Schema], encoding: str, strip_values: bool) -> Context:
    context: Context = {}
    with input_file.open("r", encoding=encoding, newline="") as in_f:
        for line_index, header_schema in enumerate(header_schemas, start=1):
            raw_line = in_f.readline()
            if raw_line == "":
                raise ValueError(
                    f"Input file has fewer than {len(header_schemas)} header lines; missing line {line_index}"
                )
            line = raw_line.rstrip("\r\n")
            context.update(parse_fixed_width_line(line, header_schema, strip_values))
    return context


def resolve_output_row(output_schema: List[Dict[str, str]], data_context: Context, header_context: Context) -> List[str]:
    row: List[str] = []
    for column in output_schema:
        source_type, field = column["source"].split(".", 1)
        if source_type == "data":
            row.append(data_context[field])
        else:  # source_type == "header"
            row.append(header_context[field])
    return row


def convert(config: Dict[str, Any]) -> None:
    input_file = Path(config["input_file"])
    output_file = Path(config["output_file"])
    input_schema = config["input_schema"]
    data_schema: Schema = input_schema["data_line"]
    header_schemas: List[Schema] = input_schema.get("header_lines", [])
    output_schema: List[Dict[str, str]] = config["output_schema"]

    delimiter = config.get("delimiter", ",")
    quotechar = config.get("quotechar", '"')
    lineterminator = config.get("lineterminator", "\n")
    include_header = config.get("include_header", True)
    encoding = config.get("encoding", "utf-8")
    strip_values = config.get("strip_values", True)

    header_context = parse_header_context(input_file, header_schemas, encoding, strip_values)
    header_line_count = len(header_schemas)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with input_file.open("r", encoding=encoding, newline="") as in_f, output_file.open(
        "w", encoding=encoding, newline=""
    ) as out_f:
        writer = csv.writer(
            out_f,
            delimiter=delimiter,
            quotechar=quotechar,
            lineterminator=lineterminator,
        )

        if include_header:
            writer.writerow([column["name"] for column in output_schema])

        for line_number, raw_line in enumerate(in_f, start=1):
            if line_number <= header_line_count:
                continue

            line = raw_line.rstrip("\r\n")
            if not line:
                continue
            data_context = parse_fixed_width_line(line, data_schema, strip_values)
            row = resolve_output_row(output_schema, data_context, header_context)
            writer.writerow(row)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert fixed-width text data to CSV based on a JSON configuration file"
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to JSON config containing file paths, input/output schemas, and CSV options",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        convert(config)
    except Exception as exc:
        raise SystemExit(f"Error: {exc}") from exc


if __name__ == "__main__":
    main()

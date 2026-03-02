#!/usr/bin/env python3
"""Convert a fixed-width file to CSV using a JSON configuration file."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


Schema = List[Dict[str, Any]]


def load_config(config_path: Path) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    validate_config(config)
    return config


def validate_schema(schema: Any, context: str) -> None:
    if not isinstance(schema, list) or not schema:
        raise ValueError(f"'{context}' must be a non-empty list")

    for idx, column in enumerate(schema, start=1):
        if not isinstance(column, dict):
            raise ValueError(f"{context} entry #{idx} must be an object")
        if "name" not in column or "width" not in column:
            raise ValueError(f"{context} entry #{idx} must include 'name' and 'width'")
        if not isinstance(column["name"], str) or not column["name"].strip():
            raise ValueError(f"{context} entry #{idx} has invalid 'name'")
        if not isinstance(column["width"], int) or column["width"] <= 0:
            raise ValueError(f"{context} entry #{idx} has invalid 'width' (must be > 0)")


def validate_config(config: Dict[str, Any]) -> None:
    required_top_level = ["input_file", "output_file", "schema"]
    missing = [k for k in required_top_level if k not in config]
    if missing:
        raise ValueError(f"Missing required config keys: {', '.join(missing)}")

    validate_schema(config["schema"], "schema")

    header_schemas = config.get("header_schemas")
    header_output_file = config.get("header_output_file")
    if header_schemas is not None:
        if not isinstance(header_schemas, list) or not header_schemas:
            raise ValueError("'header_schemas' must be a non-empty list when provided")
        for i, header_schema in enumerate(header_schemas, start=1):
            validate_schema(header_schema, f"header_schemas[{i}]")

        if not header_output_file:
            raise ValueError("'header_output_file' is required when 'header_schemas' is provided")


def parse_fixed_width_line(line: str, schema: Schema, strip_values: bool) -> List[str]:
    cursor = 0
    values: List[str] = []
    for column in schema:
        width = column["width"]
        raw = line[cursor : cursor + width]
        value = raw.strip() if strip_values else raw
        values.append(value)
        cursor += width
    return values


def write_header_csv(
    input_file: Path,
    header_schemas: List[Schema],
    header_output_file: Path,
    encoding: str,
    delimiter: str,
    quotechar: str,
    lineterminator: str,
    strip_values: bool,
) -> None:
    columns: List[str] = []
    row_values: List[str] = []

    with input_file.open("r", encoding=encoding, newline="") as in_f:
        for line_index, header_schema in enumerate(header_schemas, start=1):
            raw_line = in_f.readline()
            if raw_line == "":
                raise ValueError(
                    f"Input file has fewer than {len(header_schemas)} header lines; missing line {line_index}"
                )
            line = raw_line.rstrip("\r\n")
            parsed = parse_fixed_width_line(line, header_schema, strip_values)
            columns.extend([column["name"] for column in header_schema])
            row_values.extend(parsed)

    header_output_file.parent.mkdir(parents=True, exist_ok=True)
    with header_output_file.open("w", encoding=encoding, newline="") as out_f:
        writer = csv.writer(
            out_f,
            delimiter=delimiter,
            quotechar=quotechar,
            lineterminator=lineterminator,
        )
        writer.writerow(columns)
        writer.writerow(row_values)


def convert(config: Dict[str, Any]) -> None:
    input_file = Path(config["input_file"])
    output_file = Path(config["output_file"])
    schema: Schema = config["schema"]

    delimiter = config.get("delimiter", ",")
    quotechar = config.get("quotechar", '"')
    lineterminator = config.get("lineterminator", "\n")
    include_header = config.get("include_header", True)
    encoding = config.get("encoding", "utf-8")
    strip_values = config.get("strip_values", True)

    header_schemas: List[Schema] = config.get("header_schemas", [])
    header_output_path = config.get("header_output_file")
    header_line_count = len(header_schemas)

    if header_schemas and header_output_path:
        write_header_csv(
            input_file=input_file,
            header_schemas=header_schemas,
            header_output_file=Path(header_output_path),
            encoding=encoding,
            delimiter=delimiter,
            quotechar=quotechar,
            lineterminator=lineterminator,
            strip_values=strip_values,
        )

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
            writer.writerow([column["name"] for column in schema])

        for line_number, raw_line in enumerate(in_f, start=1):
            if line_number <= header_line_count:
                continue

            line = raw_line.rstrip("\r\n")
            if not line:
                continue
            row = parse_fixed_width_line(line, schema, strip_values)
            writer.writerow(row)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert fixed-width text data to CSV based on a JSON configuration file"
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to JSON config containing file paths, schema, and CSV options",
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

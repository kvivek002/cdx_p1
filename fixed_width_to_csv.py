#!/usr/bin/env python3
"""Convert a fixed-width file to CSV using a JSON configuration file."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def load_config(config_path: Path) -> Dict[str, Any]:
    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)
    validate_config(config)
    return config


def validate_config(config: Dict[str, Any]) -> None:
    required_top_level = ["input_file", "output_file", "schema"]
    missing = [k for k in required_top_level if k not in config]
    if missing:
        raise ValueError(f"Missing required config keys: {', '.join(missing)}")

    if not isinstance(config["schema"], list) or not config["schema"]:
        raise ValueError("'schema' must be a non-empty list")

    for idx, column in enumerate(config["schema"], start=1):
        if not isinstance(column, dict):
            raise ValueError(f"Schema entry #{idx} must be an object")
        if "name" not in column or "width" not in column:
            raise ValueError(f"Schema entry #{idx} must include 'name' and 'width'")
        if not isinstance(column["name"], str) or not column["name"].strip():
            raise ValueError(f"Schema entry #{idx} has invalid 'name'")
        if not isinstance(column["width"], int) or column["width"] <= 0:
            raise ValueError(f"Schema entry #{idx} has invalid 'width' (must be > 0)")


def parse_fixed_width_line(line: str, schema: List[Dict[str, Any]], strip_values: bool) -> List[str]:
    cursor = 0
    values: List[str] = []
    for column in schema:
        width = column["width"]
        raw = line[cursor : cursor + width]
        value = raw.strip() if strip_values else raw
        values.append(value)
        cursor += width
    return values


def convert(config: Dict[str, Any]) -> None:
    input_file = Path(config["input_file"])
    output_file = Path(config["output_file"])
    schema = config["schema"]

    delimiter = config.get("delimiter", ",")
    quotechar = config.get("quotechar", '"')
    lineterminator = config.get("lineterminator", "\n")
    include_header = config.get("include_header", True)
    encoding = config.get("encoding", "utf-8")
    strip_values = config.get("strip_values", True)

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

        for raw_line in in_f:
            line = raw_line.rstrip("\r\n")
            if not line:
                continue
            row = parse_fixed_width_line(line, schema, strip_values)
            # All values are treated as strings by default in csv.writer.
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

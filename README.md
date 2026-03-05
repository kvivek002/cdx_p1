# Fixed Width to CSV Converter

`fixed_width_to_csv.py` converts fixed-width text records into CSV using a JSON configuration file.

## Usage

```bash
python3 fixed_width_to_csv.py sample_config.json --log-level INFO --log-format text
```

## Config model

The config uses two schema sections:

- `input_schema`: describes how to parse fixed-width input lines.
- `output_schema`: describes what columns to write in output CSV and where values come from.

This lets you parse many fields, drop some, add header values, and apply cleansing transforms.

### Required top-level keys

- `input_file`
- `output_file`
- `input_schema`
- `output_schema`

### `input_schema`

- `data_line` (required): fixed-width schema for normal data records.
- `header_lines` (optional): list of fixed-width schemas, one per header line at file start.

Fixed-width schema item format:

```json
{ "name": "field_name", "width": 10 }
```

### `output_schema`

Output column definition format:

```json
{
  "name": "amount",
  "source": "data.raw_amount",
  "transforms": [
    { "type": "implied_decimal", "scale": 2 }
  ]
}
```

`source` must be one of:
- `data.<field>` — field from parsed data line
- `header.<field>` — field from parsed header lines

Supported built-in transforms:
- `trim` (`mode`: `both`|`left`|`right`)
- `upper`
- `lower`
- `implied_decimal` (`scale` integer >= 0, e.g. `13` digits with `scale: 2` => decimal with 2 fraction digits)

Custom transform plugin:

```json
{ "type": "custom", "module": "my_transforms", "function": "transform_value" }
```

Custom function signature:

```python
def transform_value(value: str, transform_config: dict, data_context: dict, header_context: dict) -> str:
    ...
```

### Optional runtime keys

- `encoding` (default: `utf-8`)
- `delimiter` (default: `,`)
- `quotechar` (default: `"`)
- `lineterminator` (default: `\n`)
- `include_header` (default: `true`)
- `strip_values` (default: `true`)
- `progress_every` (default: `0`; if >0 logs progress every N records)

## Logging

A reusable `logging_utils.py` module provides production-style logging setup for this and other scripts:

- log level selection (`--log-level`)
- text/json formats (`--log-format`)
- optional rotating file logs (`--log-file`)

## Example scenario

Input includes:
- two fixed-width header lines
- a 13-digit amount column with implied 2 decimal places

Sample input:

```text
20250101DATA
LEGACYSYS 000123
0000000123Alice Johnson       usa0000001250000Y
0000000456Bob Smith           can0000000999999N
```

Output CSV:

```csv
account_id,name,country,amount,file_date,batch_id
0000000123,Alice Johnson,USA,12500.00,20250101,000123
0000000456,Bob Smith,CAN,9999.99,20250101,000123
```

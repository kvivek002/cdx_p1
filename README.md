# Fixed Width to CSV Converter

`fixed_width_to_csv.py` converts fixed-width text records into CSV using a JSON configuration file.

## Usage

```bash
python3 fixed_width_to_csv.py sample_config.json
```

## Config model (redesigned)

The config now uses two distinct schema sections:

- `input_schema`: describes how to parse fixed-width input lines.
- `output_schema`: describes what columns to write in output CSV and where values come from.

This allows you to:
- keep extra columns in fixed-width input parsing,
- remove unwanted columns from output,
- and inject header-line fields into each output row.

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

A list of output column definitions:

```json
{ "name": "output_col", "source": "data.account_id" }
```

`source` must be one of:
- `data.<field>` — field from parsed data line
- `header.<field>` — field from parsed header lines

### Optional CSV/runtime keys

- `encoding` (default: `utf-8`)
- `delimiter` (default: `,`)
- `quotechar` (default: `"`)
- `lineterminator` (default: `\n`)
- `include_header` (default: `true`)
- `strip_values` (default: `true`)

All values are emitted as strings.

## Example scenario

Input includes:
- 2 fixed-width header lines
- data lines that include an `internal_flag` column

Output includes:
- selected data columns only (drops `internal_flag`)
- adds `file_date` and `batch_id` from header lines

Sample input:

```text
20250101DATA
LEGACYSYS 000123
0000000123Alice Johnson       USA000000012500Y
0000000456Bob Smith           CAN000000009999N
```

Output CSV:

```csv
account_id,name,country,balance,file_date,batch_id
0000000123,Alice Johnson,USA,000000012500,20250101,000123
0000000456,Bob Smith,CAN,000000009999,20250101,000123
```

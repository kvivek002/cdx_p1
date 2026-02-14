# Fixed Width to CSV Converter

`fixed_width_to_csv.py` converts fixed-width text records into CSV using a JSON configuration file.

## Usage

```bash
python3 fixed_width_to_csv.py sample_config.json
```

## JSON configuration

Required keys:
- `input_file`: path to fixed-width input file.
- `output_file`: path to CSV output file.
- `schema`: list of columns, each with:
  - `name`: column name.
  - `width`: fixed field width (integer > 0).

Optional keys:
- `encoding` (default: `utf-8`)
- `delimiter` (default: `,`)
- `quotechar` (default: `"`)
- `lineterminator` (default: `\n`)
- `include_header` (default: `true`)
- `strip_values` (default: `true`, trims whitespace for each parsed field)

All parsed column values are written as strings.

## Example input

Given schema widths `10,20,3,12`, a line like:

```text
0000000123Alice Johnson       USA000000012500
```

is parsed into:

```csv
account_id,name,country,balance
0000000123,Alice Johnson,USA,000000012500
```

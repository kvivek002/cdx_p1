# Fixed Width to CSV Converter

`fixed_width_to_csv.py` converts fixed-width text records into CSV using a JSON configuration file.

## Usage

```bash
python3 fixed_width_to_csv.py sample_config.json
```

## JSON configuration

Required keys:
- `input_file`: path to fixed-width input file.
- `output_file`: path to data CSV output file.
- `schema`: list of data columns, each with:
  - `name`: column name.
  - `width`: fixed field width (integer > 0).

Optional keys:
- `encoding` (default: `utf-8`)
- `delimiter` (default: `,`)
- `quotechar` (default: `"`)
- `lineterminator` (default: `\n`)
- `include_header` (default: `true`)
- `strip_values` (default: `true`, trims whitespace for each parsed field)

### Header-line support

If your input file starts with fixed-width header lines (for example, first two lines), you can configure a separate schema for each header line and generate a dedicated header CSV:

- `header_schemas`: list of per-line schemas; each element is a schema list for that header line.
- `header_output_file`: output path for header CSV.

When `header_schemas` is provided:
- those lines are parsed using the per-line schemas,
- `header_output_file` is written with one header row (column names) and one data row (parsed values),
- header lines are skipped from the main data CSV conversion.

All parsed column values are written as strings.

## Example input

Given:
- header line 1 schema widths: `8,4`
- header line 2 schema widths: `10,6`
- data schema widths: `10,20,3,12`

and input:

```text
20250101DATA
LEGACYSYS 000123
0000000123Alice Johnson       USA000000012500
```

outputs:

`header.csv`

```csv
file_date,file_type,source_system,batch_id
20250101,DATA,LEGACYSYS,000123
```

`output.csv`

```csv
account_id,name,country,balance
0000000123,Alice Johnson,USA,000000012500
```

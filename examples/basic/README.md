# Basic Example

What it shows: rank AWS EU regions by carbon intensity, keeping only those
within a 60ms latency budget.

## Run

```sh
carbon-region-picker --provider aws --near eu --max-latency-ms 60
```

Add `--json` to feed the result into a scheduler instead of reading the table.

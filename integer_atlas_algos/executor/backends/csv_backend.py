"""Stdlib CSV backend. Deterministic output; types coerced via the schema.

List columns (dtype ending in "[]") are stored as a JSON array in one CSV field.
"""
import csv
import json

EXT = ".csv"
COMPRESSION = "none"


def _fmt(v, dtype):
    if dtype == "bool":
        return "true" if v else "false"
    if dtype.endswith("[]"):
        return json.dumps(v)
    return str(v)


def _parse(s, dtype):
    if dtype == "bool":
        return s == "true"
    if dtype in ("double", "float64"):
        return float(s)
    if dtype == "string":
        return s
    if dtype.endswith("[]"):
        return json.loads(s)
    return int(s)  # int*, uint*, and bigint (Python ints are unbounded)


def write_table(path, schema, rows):
    names = [n for n, _ in schema]
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(names)
        for r in rows:
            w.writerow([_fmt(r[n], dt) for n, dt in schema])


class Writer:
    """Streaming writer: write parts one at a time without buffering the whole file."""

    def __init__(self, path, schema):
        self.schema = schema
        self.f = open(path, "w", newline="")
        self.w = csv.writer(self.f)
        self.w.writerow([n for n, _ in schema])

    def write_table(self, rows):
        for r in rows:
            self.w.writerow([_fmt(r[n], dt) for n, dt in self.schema])

    def close(self):
        self.f.close()


def open_writer(path, schema):
    return Writer(path, schema)


def read_table(path, schema):
    dtypes = dict(schema)
    out = []
    with open(path, newline="") as f:
        rd = csv.reader(f)
        header = next(rd)
        for row in rd:
            out.append({n: _parse(v, dtypes.get(n, "int64")) for n, v in zip(header, row)})
    return out


def count_rows(path):
    with open(path) as f:
        return max(0, sum(1 for _ in f) - 1)

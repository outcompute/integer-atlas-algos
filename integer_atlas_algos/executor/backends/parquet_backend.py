"""Parquet backend (pyarrow). The real shard format.

Exercised only when pyarrow is installed; the control flow it plugs into is
covered by the CSV-backed tests.
"""
EXT = ".parquet"
COMPRESSION = "zstd"


def _arrow_types():
    import pyarrow as pa
    return {
        "int8": pa.int8(), "int16": pa.int16(), "int32": pa.int32(), "int64": pa.int64(),
        "uint8": pa.uint8(), "uint16": pa.uint16(), "uint32": pa.uint32(), "uint64": pa.uint64(),
        "bool": pa.bool_(), "double": pa.float64(), "float64": pa.float64(),
        # bigint values can exceed any fixed width, so store them as decimal strings.
        "string": pa.string(), "bigint": pa.string(),
    }


def _rows_to_table(schema, rows):
    import pyarrow as pa

    t = _arrow_types()
    cols = {n: [] for n, _ in schema}
    for r in rows:
        for n, dt in schema:
            cols[n].append(str(r[n]) if dt == "bigint" else r[n])
    arrays = [pa.array(cols[n], type=t[dt]) for n, dt in schema]
    return pa.table(arrays, names=[n for n, _ in schema])


def write_table(path, schema, rows):
    import pyarrow.parquet as pq

    pq.write_table(_rows_to_table(schema, rows), path, compression=COMPRESSION)


class Writer:
    """Streaming writer: each part becomes a row group; memory stays bounded."""

    def __init__(self, path, schema):
        import pyarrow.parquet as pq

        self.schema = schema
        self._pq = pq
        self._writer = None
        self._path = path

    def write_table(self, rows):
        table = _rows_to_table(self.schema, rows)
        if self._writer is None:
            self._writer = self._pq.ParquetWriter(self._path, table.schema,
                                                  compression=COMPRESSION)
        self._writer.write_table(table)

    def close(self):
        if self._writer is not None:
            self._writer.close()


def open_writer(path, schema):
    return Writer(path, schema)


def read_table(path, schema):
    import pyarrow.parquet as pq

    cols = pq.read_table(path).to_pydict()
    dtypes = dict(schema)
    n = len(next(iter(cols.values()))) if cols else 0
    rows = []
    for i in range(n):
        row = {}
        for k in cols:
            v = cols[k][i]
            if dtypes.get(k) == "bigint" and v is not None:
                v = int(v)  # stored as decimal string; restore exact integer
            row[k] = v
        rows.append(row)
    return rows


def count_rows(path):
    import pyarrow.parquet as pq

    return pq.ParquetFile(path).metadata.num_rows

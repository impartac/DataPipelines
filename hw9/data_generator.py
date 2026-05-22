import os
import time
import json
import io
import argparse
import requests
import duckdb
import mysql.connector
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.csv as pa_csv

from config import (
    TPCH_SCALE_FACTOR,
    DATA_DIR,
    STARROCKS_HOST,
    STARROCKS_PORT,
    STARROCKS_USER,
    STARROCKS_PASSWORD,
    STARROCKS_DATABASE,
)

TPCH_TABLES = [
    "region",
    "nation",
    "supplier",
    "customer",
    "part",
    "partsupp",
    "orders",
    "lineitem",
]

TPCH_SF1_COUNTS = {
    "region": 5, "nation": 25, "supplier": 10_000, "customer": 150_000,
    "part": 200_000, "partsupp": 800_000, "orders": 1_500_000, "lineitem": 6_001_215,
}

STARROCKS_FE_HTTP = 8030
STARROCKS_BE_HTTP = 8040
STREAM_LOAD_CHUNK_ROWS = 200_000


def generate_tpch_parquet(
    scale_factor: int = TPCH_SCALE_FACTOR,
    output_dir: str = DATA_DIR,
) -> None:
    os.makedirs(output_dir, exist_ok=True)
    print(f"[generate] TPC-H SF={scale_factor} → {output_dir}")

    con = duckdb.connect()
    con.execute("INSTALL tpch; LOAD tpch;")
    con.execute(f"CALL dbgen(sf={scale_factor})")

    total_rows = 0
    for table in TPCH_TABLES:
        path = os.path.join(output_dir, f"{table}.parquet")
        if os.path.exists(path):
            existing_rows = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            size_mb = os.path.getsize(path) / 1024 / 1024
            print(f"  {table:10s}  skip (already exists, {existing_rows:>9,} rows, {size_mb:.1f} MB)")
            total_rows += existing_rows
            continue

        row_count = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        t0 = time.perf_counter()
        con.execute(f"COPY {table} TO '{path}' (FORMAT PARQUET, COMPRESSION 'zstd')")
        elapsed = time.perf_counter() - t0
        size_mb = os.path.getsize(path) / 1024 / 1024
        total_rows += row_count
        print(f"  {table:10s}  {row_count:>9,} rows  {size_mb:6.1f} MB  {elapsed:.1f}s")

    con.close()
    print(f"[generate] Done. Total rows: {total_rows:,}")


def _wait_for_starrocks(host: str, port: int, user: str, password: str, timeout: int = 120) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            conn = mysql.connector.connect(
                host=host, port=port, user=user, password=password,
                connection_timeout=5,
            )
            conn.close()
            return
        except Exception:
            time.sleep(3)
    raise TimeoutError(f"StarRocks did not become ready within {timeout}s")


def _stream_load_chunk(data: bytes, table: str, columns: str, label: str) -> int:
    url = f"http://{STARROCKS_HOST}:{STARROCKS_BE_HTTP}/api/{STARROCKS_DATABASE}/{table}/_stream_load"
    for attempt in range(5):
        hdrs = {
            "Expect": "100-continue",
            "label": f"{label}_{attempt}",
            "column_separator": "|",
            "columns": columns,
            "timeout": "3600",
        }
        try:
            resp = requests.put(
                url, data=data, headers=hdrs,
                auth=(STARROCKS_USER, STARROCKS_PASSWORD),
                allow_redirects=False, timeout=3600,
            )
            result = resp.json()
            status = result.get("Status", "")
            if status not in ("Success", "Publish Timeout"):
                raise RuntimeError(f"Stream Load failed: {result}")
            return int(result.get("NumberLoadedRows", 0))
        except (requests.exceptions.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
            if attempt < 4:
                time.sleep(5 + attempt * 3)
                continue
            raise RuntimeError(f"Stream Load connection error for {table} after {attempt+1} attempts: {e}")
    return 0


def _stream_load(parquet_path: str, table: str) -> int:
    tbl = pq.read_table(parquet_path)
    tbl = tbl.rename_columns([c.lower() for c in tbl.schema.names])
    for i, field in enumerate(tbl.schema):
        if pa.types.is_date(field.type) or pa.types.is_timestamp(field.type):
            tbl = tbl.set_column(i, field.name, tbl.column(field.name).cast(pa.string()))
    columns = ",".join(tbl.schema.names)

    nrows = len(tbl)
    base_label = f"load_{table}_{int(time.time())}"
    if nrows <= STREAM_LOAD_CHUNK_ROWS:
        buf = io.BytesIO()
        pa_csv.write_csv(tbl, buf, write_options=pa_csv.WriteOptions(
            include_header=False, delimiter="|", quoting_style="none"))
        return _stream_load_chunk(buf.getvalue(), table, columns, base_label)

    total = 0
    for chunk_idx, offset in enumerate(range(0, nrows, STREAM_LOAD_CHUNK_ROWS)):
        chunk = tbl.slice(offset, STREAM_LOAD_CHUNK_ROWS)
        buf = io.BytesIO()
        pa_csv.write_csv(chunk, buf, write_options=pa_csv.WriteOptions(
            include_header=False, delimiter="|", quoting_style="none"))
        label = f"{base_label}_c{chunk_idx}"
        chunk_rows = _stream_load_chunk(buf.getvalue(), table, columns, label)
        total += chunk_rows
        print(f"    chunk {chunk_idx+1}/{(nrows+STREAM_LOAD_CHUNK_ROWS-1)//STREAM_LOAD_CHUNK_ROWS}: {chunk_rows:,} rows", flush=True)
    return total


def load_into_starrocks(parquet_dir: str = DATA_DIR) -> None:
    print(f"[load] StarRocks at {STARROCKS_HOST}:{STARROCKS_PORT} (Stream Load → :{STARROCKS_FE_HTTP})")
    _wait_for_starrocks(STARROCKS_HOST, STARROCKS_PORT, STARROCKS_USER, STARROCKS_PASSWORD)

    conn = mysql.connector.connect(
        host=STARROCKS_HOST, port=STARROCKS_PORT,
        user=STARROCKS_USER, password=STARROCKS_PASSWORD,
        connection_timeout=30, autocommit=True,
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {STARROCKS_DATABASE}")
    cursor.close()
    conn.close()

    _create_starrocks_tables()

    conn = mysql.connector.connect(
        host=STARROCKS_HOST, port=STARROCKS_PORT,
        user=STARROCKS_USER, password=STARROCKS_PASSWORD,
        database=STARROCKS_DATABASE, connection_timeout=30, autocommit=True,
    )
    for table in TPCH_TABLES:
        path = os.path.join(parquet_dir, f"{table}.parquet")
        if not os.path.exists(path):
            print(f"  [WARN] {path} not found, skipping {table}")
            continue

        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        existing = cursor.fetchone()[0]
        cursor.close()

        expected = TPCH_SF1_COUNTS.get(table, -1)
        if existing == expected:
            print(f"  {table:10s}  skip ({existing:,} rows)")
            continue
        if existing > 0:
            cursor = conn.cursor()
            cursor.execute(f"TRUNCATE TABLE {table}")
            cursor.close()
            print(f"  {table:10s}  truncated partial load ({existing:,} rows), reloading...")

        size_mb = os.path.getsize(path) / 1024 / 1024
        print(f"  {table:10s}  {size_mb:.1f} MB → stream load...", end=" ", flush=True)
        t0 = time.perf_counter()
        loaded = _stream_load(path, table)
        elapsed = time.perf_counter() - t0
        print(f"{loaded:,} rows in {elapsed:.1f}s ({size_mb / elapsed:.1f} MB/s)")

    conn.close()
    print("[load] Done.")


def _create_starrocks_tables() -> None:
    ddl_path = os.path.join(os.path.dirname(__file__), "sql", "starrocks", "create_tables.sql")
    if not os.path.exists(ddl_path):
        raise FileNotFoundError(f"DDL file not found: {ddl_path}")

    with open(ddl_path, encoding="utf-8") as f:
        raw = f.read()

    conn = mysql.connector.connect(
        host=STARROCKS_HOST,
        port=STARROCKS_PORT,
        user=STARROCKS_USER,
        password=STARROCKS_PASSWORD,
        database=STARROCKS_DATABASE,
        connection_timeout=30,
        autocommit=True,
    )
    cursor = conn.cursor()
    def _strip_leading_comments(s: str) -> str:
        lines = s.splitlines()
        return "\n".join(l for l in lines if not l.strip().startswith("--")).strip()

    statements = [_strip_leading_comments(s) for s in raw.split(";")]
    statements = [s for s in statements if s]
    for stmt in statements:
        cursor.execute(stmt)

    cursor.close()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TPC-H data generator for hw9")
    parser.add_argument("--generate-only", action="store_true")
    parser.add_argument("--load-only", action="store_true")
    parser.add_argument("--sf", type=int, default=TPCH_SCALE_FACTOR)
    args = parser.parse_args()

    if not args.load_only:
        generate_tpch_parquet(scale_factor=args.sf)
    if not args.generate_only:
        load_into_starrocks()

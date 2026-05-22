import os
import shutil
import statistics
import time
from dataclasses import dataclass
from typing import List

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import col, count, sum as spark_sum

from config import (
    BASE_ROWS,
    BENCHMARK_ITERATIONS,
    DELTA_WAREHOUSE,
    FRACTIONS,
    HUDI_WAREHOUSE,
    ICEBERG_WAREHOUSE,
)
from data_generator import generate_dataframe

_HUDI_BASE = {
    "hoodie.datasource.write.recordkey.field":  "doc_id",
    "hoodie.datasource.write.precombine.field": "amount",
    "hoodie.datasource.write.operation":        "bulk_insert",
    "hoodie.datasource.write.table.type":       "COPY_ON_WRITE",
    "hoodie.bulkinsert.shuffle.parallelism":    "4",
}


@dataclass
class WriteResult:
    format_name:      str
    fraction:         float
    n_rows:           int
    write_time_sec:   float
    overwrite_time_sec: float


@dataclass
class ReadResult:
    format_name:    str
    scan_time_sec:  float
    filter_time_sec: float
    agg_time_sec:   float


@dataclass
class SizeResult:
    format_name: str
    size_bytes:  int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _table_path(fmt: str, name: str) -> str:
    if fmt == "delta":
        return os.path.join(DELTA_WAREHOUSE, name)
    if fmt == "hudi":
        return os.path.join(HUDI_WAREHOUSE, name)
    return os.path.join(ICEBERG_WAREHOUSE, "default", name)


def _dir_size(path: str) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def _write(spark: SparkSession, fmt: str, df: DataFrame, mode: str, name: str):
    if fmt == "iceberg":
        df.write.format("iceberg").mode(mode).saveAsTable(f"local.default.{name}")
    elif fmt == "delta":
        df.write.format("delta").mode(mode).save(_table_path(fmt, name))
    else:
        opts = {**_HUDI_BASE, "hoodie.table.name": name}
        df.write.format("hudi").options(**opts).mode(mode).save(
            _table_path(fmt, name)
        )


def _read(spark: SparkSession, fmt: str, name: str) -> DataFrame:
    if fmt == "iceberg":
        return spark.table(f"local.default.{name}")
    if fmt == "delta":
        return spark.read.format("delta").load(_table_path(fmt, name))
    return spark.read.format("hudi").load(_table_path(fmt, name))


def _clear(spark: SparkSession, fmt: str, name: str):
    if fmt == "iceberg":
        spark.sql(f"DROP TABLE IF EXISTS local.default.{name}")
    else:
        path = _table_path(fmt, name)
        if os.path.exists(path):
            shutil.rmtree(path)


# ---------------------------------------------------------------------------
# Benchmarks
# ---------------------------------------------------------------------------

def run_write_benchmark(spark: SparkSession, fmt: str) -> List[WriteResult]:
    if fmt == "iceberg":
        spark.sql("CREATE NAMESPACE IF NOT EXISTS local.default")

    results = []
    for fraction in FRACTIONS:
        n_rows     = int(BASE_ROWS * fraction)
        table_name = f"bench_write_{int(fraction * 100)}"

        write_times     = []
        overwrite_times = []

        for _ in range(BENCHMARK_ITERATIONS):
            _clear(spark, fmt, table_name)
            df = generate_dataframe(spark, n_rows)
            df.cache()

            t0 = time.time()
            _write(spark, fmt, df, "overwrite", table_name)
            write_times.append(time.time() - t0)

            t0 = time.time()
            _write(spark, fmt, df, "overwrite", table_name)
            overwrite_times.append(time.time() - t0)

            df.unpersist()

        results.append(WriteResult(
            format_name=fmt,
            fraction=fraction,
            n_rows=n_rows,
            write_time_sec=round(statistics.median(write_times), 2),
            overwrite_time_sec=round(statistics.median(overwrite_times), 2),
        ))
    return results


def run_read_benchmark(spark: SparkSession, fmt: str) -> ReadResult:
    if fmt == "iceberg":
        spark.sql("CREATE NAMESPACE IF NOT EXISTS local.default")

    table_name = f"bench_read"
    _clear(spark, fmt, table_name)
    df_full = generate_dataframe(spark, BASE_ROWS)
    _write(spark, fmt, df_full, "overwrite", table_name)

    scan_times, filter_times, agg_times = [], [], []

    for _ in range(BENCHMARK_ITERATIONS):
        t0 = time.time()
        _read(spark, fmt, table_name).count()
        scan_times.append(time.time() - t0)

        t0 = time.time()
        _read(spark, fmt, table_name).filter(col("region") == "MSK").count()
        filter_times.append(time.time() - t0)

        t0 = time.time()
        (
            _read(spark, fmt, table_name)
            .groupBy("category")
            .agg(spark_sum("amount"), count("*"))
            .collect()
        )
        agg_times.append(time.time() - t0)

    return ReadResult(
        format_name=fmt,
        scan_time_sec=round(statistics.median(scan_times), 2),
        filter_time_sec=round(statistics.median(filter_times), 2),
        agg_time_sec=round(statistics.median(agg_times), 2),
    )


def measure_size(fmt: str) -> SizeResult:
    path = _table_path(fmt, "bench_read")
    return SizeResult(
        format_name=fmt,
        size_bytes=_dir_size(path) if os.path.exists(path) else 0,
    )

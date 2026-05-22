import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import List

from pyspark.sql import SparkSession

from config import (
    BASE_ROWS,
    DELTA_WAREHOUSE,
    HUDI_WAREHOUSE,
    ICEBERG_WAREHOUSE,
    N_CONCURRENT_WRITERS,
)
from data_generator import generate_dataframe

_HUDI_OPTS = {
    "hoodie.table.name":                       "concurrent_test",
    "hoodie.datasource.write.recordkey.field": "doc_id",
    "hoodie.datasource.write.precombine.field":"amount",
    "hoodie.datasource.write.operation":       "bulk_insert",
    "hoodie.datasource.write.table.type":      "COPY_ON_WRITE",
    "hoodie.bulkinsert.shuffle.parallelism":   "2",
}


@dataclass
class ConcurrentTestResult:
    format_name:   str
    expected_rows: int
    actual_rows:   int
    successes:     int
    failures:      int
    total_sec:     float
    errors:        List[str] = field(default_factory=list)


def _clear(spark: SparkSession, fmt: str) -> None:
    if fmt == "iceberg":
        spark.sql("DROP TABLE IF EXISTS local.default.concurrent_test")
        spark.sql("CREATE NAMESPACE IF NOT EXISTS local.default")
    elif fmt == "delta":
        path = os.path.join(DELTA_WAREHOUSE, "concurrent_test")
        if os.path.exists(path):
            shutil.rmtree(path)
    else:
        path = os.path.join(HUDI_WAREHOUSE, "concurrent_test")
        if os.path.exists(path):
            shutil.rmtree(path)


def _write_one(spark: SparkSession, fmt: str, df) -> None:
    if fmt == "iceberg":
        df.write.format("iceberg").mode("append").saveAsTable(
            "local.default.concurrent_test"
        )
    elif fmt == "delta":
        df.write.format("delta").mode("append").save(
            os.path.join(DELTA_WAREHOUSE, "concurrent_test")
        )
    else:
        (
            df.write
            .format("hudi")
            .options(**_HUDI_OPTS)
            .mode("append")
            .save(os.path.join(HUDI_WAREHOUSE, "concurrent_test"))
        )


def _count_table(spark: SparkSession, fmt: str) -> int:
    if fmt == "iceberg":
        return spark.table("local.default.concurrent_test").count()
    elif fmt == "delta":
        return spark.read.format("delta").load(
            os.path.join(DELTA_WAREHOUSE, "concurrent_test")
        ).count()
    else:
        return spark.read.format("hudi").load(
            os.path.join(HUDI_WAREHOUSE, "concurrent_test")
        ).count()


def run_concurrent_test(spark: SparkSession, fmt: str) -> ConcurrentTestResult:
    rows_per_writer = BASE_ROWS // N_CONCURRENT_WRITERS
    expected = rows_per_writer * N_CONCURRENT_WRITERS

    _clear(spark, fmt)

    # Pre-generate and cache all partitions (distinct id ranges → no upsert conflict)
    partitions = [
        generate_dataframe(spark, rows_per_writer, id_offset=i * rows_per_writer)
        for i in range(N_CONCURRENT_WRITERS)
    ]
    for df in partitions:
        df.cache()

    successes = 0
    failures  = 0
    errors: List[str] = []

    t0 = time.time()

    def _task(writer_id: int):
        try:
            _write_one(spark, fmt, partitions[writer_id])
            return True, ""
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)

    with ThreadPoolExecutor(max_workers=N_CONCURRENT_WRITERS) as pool:
        futs = {pool.submit(_task, i): i for i in range(N_CONCURRENT_WRITERS)}
        for fut in as_completed(futs):
            ok, err = fut.result()
            if ok:
                successes += 1
            else:
                failures += 1
                errors.append(err)

    total_sec = round(time.time() - t0, 2)

    for df in partitions:
        df.unpersist()

    try:
        actual = _count_table(spark, fmt)
    except Exception:  # noqa: BLE001
        actual = 0

    return ConcurrentTestResult(
        format_name=fmt,
        expected_rows=expected,
        actual_rows=actual,
        successes=successes,
        failures=failures,
        total_sec=total_sec,
        errors=errors,
    )

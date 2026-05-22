import argparse
import os
import sys

from config import (
    DELTA_WAREHOUSE,
    HUDI_WAREHOUSE,
    ICEBERG_WAREHOUSE,
    RESULTS_DIR,
    SPARK_CONFIGS,
)


def build_spark(fmt: str):
    from pyspark.sql import SparkSession

    try:
        SparkSession.builder.getOrCreate().stop()
    except Exception:
        pass

    builder = SparkSession.builder
    for k, v in SPARK_CONFIGS[fmt].items():
        builder = builder.config(k, v)
    return builder.getOrCreate()


def parse_args():
    p = argparse.ArgumentParser(
        description="hw7: Apache Iceberg / Delta Lake / Apache Hudi benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--skip-concurrent",
        action="store_true",
        help="Skip concurrent write experiments",
    )
    p.add_argument(
        "--skip-benchmark",
        action="store_true",
        help="Skip performance benchmarks",
    )
    p.add_argument(
        "--formats",
        nargs="+",
        default=["iceberg", "delta", "hudi"],
        choices=["iceberg", "delta", "hudi"],
        help="Formats to test (default: all three)",
    )
    return p.parse_args()


def main():
    args = parse_args()

    for d in (RESULTS_DIR, ICEBERG_WAREHOUSE, DELTA_WAREHOUSE, HUDI_WAREHOUSE):
        os.makedirs(d, exist_ok=True)

    print("=" * 70)
    print("hw7: Table Format Benchmark — Iceberg / Delta Lake / Hudi")
    print("=" * 70)

    concurrent_results = []
    write_results      = []
    read_results       = []
    size_results       = []

    for fmt in args.formats:
        print(f"\n{'─' * 60}")
        print(f"  Format: {fmt.upper()}")
        print(f"{'─' * 60}")

        spark = build_spark(fmt)

        if not args.skip_concurrent:
            from concurrent_writer import run_concurrent_test
            print(f"  [concurrent] testing {fmt}...")
            result = run_concurrent_test(spark, fmt)
            concurrent_results.append(result)
            print(
                f"    expected={result.expected_rows:,}  "
                f"actual={result.actual_rows:,}  "
                f"ok={result.successes}  fail={result.failures}  "
                f"loss={result.expected_rows - result.actual_rows:,}  "
                f"time={result.total_sec}s"
            )

        if not args.skip_benchmark:
            from benchmark import measure_size, run_read_benchmark, run_write_benchmark
            print(f"  [write bench] {fmt}...")
            wr = run_write_benchmark(spark, fmt)
            write_results.extend(wr)
            for r in wr:
                print(
                    f"    {int(r.fraction * 100):3d}%  "
                    f"{r.n_rows:>7,} rows  "
                    f"write={r.write_time_sec}s  "
                    f"overwrite={r.overwrite_time_sec}s"
                )

            print(f"  [read bench] {fmt}...")
            rr = run_read_benchmark(spark, fmt)
            read_results.append(rr)
            print(
                f"    scan={rr.scan_time_sec}s  "
                f"filter={rr.filter_time_sec}s  "
                f"agg={rr.agg_time_sec}s"
            )

            sr = measure_size(fmt)
            size_results.append(sr)
            print(f"    size={sr.size_bytes / 1024 / 1024:.1f} MB")

        spark.stop()

    from report_generator import save_benchmark_results, save_concurrent_results

    if concurrent_results:
        save_concurrent_results(concurrent_results, RESULTS_DIR)
        print(f"\nConcurrent results → {RESULTS_DIR}/concurrent_results.csv")

    if write_results or read_results:
        save_benchmark_results(write_results, read_results, size_results, RESULTS_DIR)
        print(f"Benchmark results  → {RESULTS_DIR}/write_benchmark.csv")
        print(f"                     {RESULTS_DIR}/read_benchmark.csv")
        print(f"                     {RESULTS_DIR}/size_results.csv")

    print("\nDone.")


if __name__ == "__main__":
    main()

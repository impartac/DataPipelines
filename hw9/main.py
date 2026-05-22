import argparse
import sys

from config import TPCH_SCALE_FACTOR, DATA_DIR, RESULTS_DIR, DEFAULT_QUERY_IDS
from data_generator import generate_tpch_parquet, load_into_starrocks
from benchmark import (
    TrinoRunner,
    StarRocksRunner,
    run_benchmark,
    save_results,
    print_summary,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="hw9: Trino vs StarRocks — TPC-H benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skip-generate",
        action="store_true",
        help="Skip DuckDB Parquet generation (use existing files in ./data/)",
    )
    parser.add_argument(
        "--skip-load",
        action="store_true",
        help="Skip loading data into StarRocks (assume tables already populated)",
    )
    parser.add_argument(
        "--queries",
        type=str,
        default=",".join(str(q) for q in DEFAULT_QUERY_IDS),
        help=(
            "Comma-separated TPC-H query IDs to run. "
            f"Default: {','.join(str(q) for q in DEFAULT_QUERY_IDS)}"
        ),
    )
    parser.add_argument(
        "--engines",
        type=str,
        default="trino,starrocks",
        help="Engines to benchmark: 'trino', 'starrocks', or 'trino,starrocks'",
    )
    parser.add_argument(
        "--sf",
        type=int,
        default=TPCH_SCALE_FACTOR,
        help="TPC-H scale factor for data generation (default: 1)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    query_ids = [int(q.strip()) for q in args.queries.split(",") if q.strip()]
    engines   = [e.strip().lower() for e in args.engines.split(",") if e.strip()]

    print("=" * 60)
    print("  hw9 — Trino vs StarRocks TPC-H Benchmark")
    print("=" * 60)
    print(f"  Scale factor : SF={args.sf}")
    print(f"  Queries      : {query_ids}")
    print(f"  Engines      : {engines}")
    print()


    if not args.skip_generate:
        generate_tpch_parquet(scale_factor=args.sf, output_dir=DATA_DIR)
    else:
        print("[main] Skipping data generation (--skip-generate)\n")


    if "starrocks" in engines and not args.skip_load:
        load_into_starrocks(parquet_dir=DATA_DIR)
    else:
        print("[main] Skipping StarRocks load (--skip-load or StarRocks not in engines)\n")

    all_results = []


    if "trino" in engines:
        print("\n[main] Benchmarking Trino ...")
        try:
            runner = TrinoRunner()
            results = run_benchmark("Trino", runner, query_ids)
            runner.close()
            all_results.extend(results)
        except Exception as exc:
            print(f"[main] Cannot connect to Trino: {exc}")
            print("       → Start with: docker compose up -d trino")


    if "starrocks" in engines:
        print("\n[main] Benchmarking StarRocks ...")
        try:
            runner = StarRocksRunner()
            results = run_benchmark("StarRocks", runner, query_ids)
            runner.close()
            all_results.extend(results)
        except Exception as exc:
            print(f"[main] Cannot connect to StarRocks: {exc}")
            print("       → Start with: docker compose up -d starrocks")


    if not all_results:
        print("\n[main] No results collected. Check that the engines are running.")
        sys.exit(1)

    save_results(all_results, output_dir=RESULTS_DIR)
    print_summary(all_results)


if __name__ == "__main__":
    main()

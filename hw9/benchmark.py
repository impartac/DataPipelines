import time
import json
import csv
import os
import statistics
from dataclasses import dataclass, field
from typing import List, Optional

import trino
import mysql.connector
from tabulate import tabulate

from config import (
    TRINO_HOST,
    TRINO_PORT,
    TRINO_USER,
    TRINO_CATALOG,
    TRINO_SCHEMA,
    STARROCKS_HOST,
    STARROCKS_PORT,
    STARROCKS_USER,
    STARROCKS_PASSWORD,
    STARROCKS_DATABASE,
    BENCHMARK_ITERATIONS,
    QUERY_TIMEOUT_SECONDS,
    RESULTS_DIR,
)
from sql.queries import TPCH_QUERIES



@dataclass
class BenchmarkResult:
    engine: str
    query_id: int
    cold_time: float
    warm_times: List[float] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def mean(self) -> float:
        return statistics.mean(self.warm_times) if self.warm_times else 0.0

    @property
    def median(self) -> float:
        return statistics.median(self.warm_times) if self.warm_times else 0.0

    @property
    def min_time(self) -> float:
        return min(self.warm_times) if self.warm_times else 0.0

    @property
    def max_time(self) -> float:
        return max(self.warm_times) if self.warm_times else 0.0

    def to_dict(self) -> dict:
        return {
            "engine":        self.engine,
            "query_id":      self.query_id,
            "cold_s":        round(self.cold_time, 3),
            "warm_mean_s":   round(self.mean, 3),
            "warm_median_s": round(self.median, 3),
            "warm_min_s":    round(self.min_time, 3),
            "warm_max_s":    round(self.max_time, 3),
            "error":         self.error,
        }



class TrinoRunner:
    def __init__(self):
        self._conn = trino.dbapi.connect(
            host=TRINO_HOST,
            port=TRINO_PORT,
            user=TRINO_USER,
            catalog=TRINO_CATALOG,
            schema=TRINO_SCHEMA,
            request_timeout=QUERY_TIMEOUT_SECONDS,
        )

    def execute(self, sql: str) -> float:
        cursor = self._conn.cursor()
        t0 = time.perf_counter()
        cursor.execute(sql)
        cursor.fetchall()
        elapsed = time.perf_counter() - t0
        cursor.close()
        return elapsed

    def close(self):
        self._conn.close()


class StarRocksRunner:

    def __init__(self):
        self._conn = mysql.connector.connect(
            host=STARROCKS_HOST,
            port=STARROCKS_PORT,
            user=STARROCKS_USER,
            password=STARROCKS_PASSWORD,
            database=STARROCKS_DATABASE,
            connection_timeout=60,
            autocommit=True,
        )

    def execute(self, sql: str) -> float:
        cursor = self._conn.cursor()
        t0 = time.perf_counter()
        cursor.execute(sql)
        cursor.fetchall()
        elapsed = time.perf_counter() - t0
        cursor.close()
        return elapsed

    def close(self):
        self._conn.close()


def _run_single_query(
    runner,
    sql: str,
    iterations: int = BENCHMARK_ITERATIONS,
) -> tuple[float, list[float]]:
    cold_time = runner.execute(sql)
    warm_times = [runner.execute(sql) for _ in range(iterations)]
    return cold_time, warm_times


def run_benchmark(
    engine_name: str,
    runner,
    query_ids: List[int],
) -> List[BenchmarkResult]:
    results: List[BenchmarkResult] = []

    for qid in query_ids:
        if qid not in TPCH_QUERIES:
            print(f"  [WARN] Q{qid:02d} not defined, skipping")
            continue

        sql = TPCH_QUERIES[qid]
        print(f"  Q{qid:02d} ...", end=" ", flush=True)

        try:
            cold, warm = _run_single_query(runner, sql)
            result = BenchmarkResult(
                engine=engine_name,
                query_id=qid,
                cold_time=cold,
                warm_times=warm,
            )
            print(
                f"cold={cold:.2f}s  "
                f"warm: min={result.min_time:.2f}s  "
                f"med={result.median:.2f}s  "
                f"max={result.max_time:.2f}s"
            )
        except Exception as exc:
            print(f"ERROR — {exc}")
            result = BenchmarkResult(
                engine=engine_name,
                query_id=qid,
                cold_time=0.0,
                error=str(exc),
            )

        results.append(result)

    return results


def save_results(results: List[BenchmarkResult], output_dir: str = RESULTS_DIR) -> None:
    os.makedirs(output_dir, exist_ok=True)
    rows = [r.to_dict() for r in results]

    csv_path = os.path.join(output_dir, "benchmark_results.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    print(f"\nResults → {csv_path}")

    json_path = os.path.join(output_dir, "benchmark_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
    print(f"Results → {json_path}")


def print_summary(results: List[BenchmarkResult]) -> None:
    trino_map = {r.query_id: r for r in results if r.engine == "Trino"     and not r.error}
    sr_map    = {r.query_id: r for r in results if r.engine == "StarRocks" and not r.error}
    all_qids  = sorted(set(list(trino_map) + list(sr_map)))

    print("\n" + "=" * 72)
    print("  BENCHMARK RESULTS — TPC-H SF=1  (warm median, seconds)")
    print("=" * 72)

    table_rows = []
    for qid in all_qids:
        t = trino_map.get(qid)
        s = sr_map.get(qid)
        t_val = f"{t.median:.3f}" if t else "N/A"
        s_val = f"{s.median:.3f}" if s else "N/A"
        ratio = f"{t.median / s.median:.1f}x" if (t and s and s.median > 0) else "—"
        table_rows.append([f"Q{qid:02d}", t_val, s_val, ratio])

    print(tabulate(
        table_rows,
        headers=["Query", "Trino (s)", "StarRocks (s)", "Trino / SR"],
        tablefmt="rounded_outline",
    ))

    scale = 0.05
    max_bar = 60
    print("\n  Bar chart  (1 char ≈ 0.05 s,  █ = Trino,  ░ = StarRocks)")
    print("  " + "─" * 64)
    for qid in all_qids:
        t = trino_map.get(qid)
        s = sr_map.get(qid)
        t_bar = min(int(t.median / scale), max_bar) if t else 0
        s_bar = min(int(s.median / scale), max_bar) if s else 0
        print(f"  Q{qid:02d} T |{'█' * t_bar}")
        print(f"       SR|{'░' * s_bar}")
    print()

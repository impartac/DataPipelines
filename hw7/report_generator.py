import csv
import json
import os
from typing import List

from benchmark import ReadResult, SizeResult, WriteResult
from concurrent_writer import ConcurrentTestResult


def _append_csv(path: str, fields, rows):
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if not file_exists:
            w.writeheader()
        w.writerows(rows)


def save_concurrent_results(results: List[ConcurrentTestResult], results_dir: str):
    csv_path = os.path.join(results_dir, "concurrent_results.csv")
    fields   = ["format", "expected_rows", "actual_rows",
                 "successes", "failures", "data_loss", "total_sec"]
    _append_csv(csv_path, fields, [
        {
            "format":        r.format_name,
            "expected_rows": r.expected_rows,
            "actual_rows":   r.actual_rows,
            "successes":     r.successes,
            "failures":      r.failures,
            "data_loss":     r.expected_rows - r.actual_rows,
            "total_sec":     r.total_sec,
        }
        for r in results
    ])

    json_path = os.path.join(results_dir, "concurrent_results.json")
    existing = []
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    existing += [
        {
            "format":        r.format_name,
            "expected_rows": r.expected_rows,
            "actual_rows":   r.actual_rows,
            "successes":     r.successes,
            "failures":      r.failures,
            "data_loss":     r.expected_rows - r.actual_rows,
            "total_sec":     r.total_sec,
            "errors":        r.errors,
        }
        for r in results
    ]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def save_benchmark_results(
    write_results: List[WriteResult],
    read_results:  List[ReadResult],
    size_results:  List[SizeResult],
    results_dir:   str,
):
    _append_csv(
        os.path.join(results_dir, "write_benchmark.csv"),
        ["format", "fraction", "n_rows", "write_time_sec", "overwrite_time_sec"],
        [
            {
                "format":             r.format_name,
                "fraction":           r.fraction,
                "n_rows":             r.n_rows,
                "write_time_sec":     r.write_time_sec,
                "overwrite_time_sec": r.overwrite_time_sec,
            }
            for r in write_results
        ],
    )

    _append_csv(
        os.path.join(results_dir, "read_benchmark.csv"),
        ["format", "scan_time_sec", "filter_time_sec", "agg_time_sec"],
        [
            {
                "format":          r.format_name,
                "scan_time_sec":   r.scan_time_sec,
                "filter_time_sec": r.filter_time_sec,
                "agg_time_sec":    r.agg_time_sec,
            }
            for r in read_results
        ],
    )

    _append_csv(
        os.path.join(results_dir, "size_results.csv"),
        ["format", "size_bytes", "size_mb"],
        [
            {
                "format":     r.format_name,
                "size_bytes": r.size_bytes,
                "size_mb":    round(r.size_bytes / 1024 / 1024, 2),
            }
            for r in size_results
        ],
    )

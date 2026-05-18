"""
Data Processing Job
===================
Runs in two modes:
  - Local (pure Python/pandas) - for Docker demo and testing
  - Spark (PySpark) - for production cluster execution

Environment variables:
  USE_SPARK=true       - use PySpark instead of pandas
  INPUT_PATH           - path to input data directory
  OUTPUT_PATH          - path for output results
  JOB_NAME             - job identifier for logging
  PARTITION_COUNT      - number of partitions (Spark only)
"""

import os
import sys
import json
from datetime import datetime


def generate_sample_data(n: int = 10000) -> list:
    """Generate synthetic order data for processing."""
    categories = ["electronics", "clothing", "food", "furniture", "sports"]
    statuses = ["completed", "pending", "cancelled", "refunded"]
    weights = [0.6, 0.2, 0.1, 0.1]  # distribution for statuses

    import random
    random.seed(42)

    records = []
    for i in range(1, n + 1):
        status_idx = random.choices(range(4), weights=weights)[0]
        records.append({
            "order_id": f"ORD-{i:06d}",
            "customer_id": f"CUST-{random.randint(1, 1000):04d}",
            "category": random.choice(categories),
            "amount": round(random.uniform(10.0, 5000.0), 2),
            "status": statuses[status_idx],
            "created_at": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        })
    return records


def run_local_mode(input_path: str, output_path: str, job_name: str) -> dict:
    """Run ETL in local Python mode (no Spark dependency)."""
    print("Running in LOCAL mode (Python)")

    # EXTRACT
    print("\n[1/4] EXTRACT: Loading source data...")
    input_file = os.path.join(input_path, "orders.json")
    if os.path.exists(input_file):
        with open(input_file) as f:
            records = json.load(f)
        print(f"  Loaded {len(records)} records from {input_file}")
    else:
        records = generate_sample_data(10000)
        print(f"  Generated {len(records)} synthetic records")

    # TRANSFORM
    print("\n[2/4] TRANSFORM: Filtering and aggregating...")
    completed = [r for r in records if r["status"] == "completed"]
    print(f"  Filtered to {len(completed)} completed orders")

    aggregated = {}
    for r in completed:
        cat = r["category"]
        if cat not in aggregated:
            aggregated[cat] = {"count": 0, "total_amount": 0.0, "avg_amount": 0.0}
        aggregated[cat]["count"] += 1
        aggregated[cat]["total_amount"] += r["amount"]

    results = []
    for cat, data in sorted(aggregated.items()):
        data["avg_amount"] = round(data["total_amount"] / data["count"], 2)
        data["total_amount"] = round(data["total_amount"], 2)
        results.append({"category": cat, **data})

    # VALIDATE
    print("\n[3/4] VALIDATE: Running quality checks...")
    assert len(results) > 0, "No output records - processing failed"
    assert all(r["count"] > 0 for r in results), "Category with zero records"
    assert all(r["avg_amount"] > 0 for r in results), "Negative average amount"
    print(f"  Quality check PASSED: {len(results)} categories, all non-empty")

    # LOAD
    print("\n[4/4] LOAD: Writing output...")
    os.makedirs(output_path, exist_ok=True)

    report = {
        "job_name": job_name,
        "mode": "local",
        "run_timestamp": datetime.now().isoformat(),
        "input_records": len(records),
        "processed_records": len(completed),
        "output_records": len(results),
        "results": results,
    }

    out_file = os.path.join(output_path, "results.json")
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)
    print(f"  Written to: {out_file}")

    return report


def run_spark_mode(input_path: str, output_path: str, job_name: str) -> dict:
    """Run ETL using Apache Spark (PySpark)."""
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    print("Running in SPARK mode (PySpark)")

    spark = (
        SparkSession.builder
        .appName(job_name)
        .config("spark.sql.shuffle.partitions", os.environ.get("PARTITION_COUNT", "8"))
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    # EXTRACT
    print("\n[1/4] EXTRACT: Reading source data...")
    df = spark.read.json(os.path.join(input_path, "*.json"))
    total_count = df.count()
    print(f"  Loaded {total_count} records")

    # TRANSFORM
    print("\n[2/4] TRANSFORM: Aggregating by category...")
    result_df = (
        df.filter(F.col("status") == "completed")
        .groupBy("category")
        .agg(
            F.count("*").alias("count"),
            F.round(F.sum("amount"), 2).alias("total_amount"),
            F.round(F.avg("amount"), 2).alias("avg_amount"),
        )
        .orderBy("category")
    )
    result_df.show()
    processed = result_df.count()

    # LOAD
    print("\n[3/4] LOAD: Writing output...")
    os.makedirs(output_path, exist_ok=True)
    result_df.write.mode("overwrite").json(os.path.join(output_path, "results"))
    print(f"  Written to: {output_path}/results/")

    spark.stop()

    return {
        "job_name": job_name,
        "mode": "spark",
        "run_timestamp": datetime.now().isoformat(),
        "input_records": total_count,
        "output_records": processed,
    }


def main():
    job_name = os.environ.get("JOB_NAME", "data-processor")
    input_path = os.environ.get("INPUT_PATH", "/data/input")
    output_path = os.environ.get("OUTPUT_PATH", "/data/output")
    use_spark = os.environ.get("USE_SPARK", "false").lower() == "true"

    print("=" * 60)
    print("  SPARK DATA PROCESSING JOB")
    print("=" * 60)
    print(f"  Job:    {job_name}")
    print(f"  Mode:   {'Spark (PySpark)' if use_spark else 'Local (Python)'}")
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_path}")
    print(f"  Start:  {datetime.now().isoformat()}")
    print("=" * 60)

    try:
        if use_spark:
            report = run_spark_mode(input_path, output_path, job_name)
        else:
            report = run_local_mode(input_path, output_path, job_name)

        print("\n" + "=" * 60)
        print("  JOB COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"  Input records:   {report.get('input_records', 'N/A')}")
        print(f"  Processed:       {report.get('processed_records', report.get('output_records', 'N/A'))}")
        print(f"  Output records:  {report.get('output_records', 'N/A')}")
        print(f"  Finish: {datetime.now().isoformat()}")
        print("=" * 60)
        sys.exit(0)

    except Exception as e:
        print(f"\n[ERROR] Job failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

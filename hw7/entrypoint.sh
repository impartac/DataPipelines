#!/bin/bash
# Each format runs in a separate Python process so each gets its own JVM
# with the correct JAR on the classpath via PYSPARK_SUBMIT_ARGS.
set -e

RESULTS=/app/results
rm -f "$RESULTS"/*.csv "$RESULTS"/*.json

echo "========================================================"
echo "  hw7: Table Format Benchmark"
echo "  Iceberg 1.5.2 | Delta 3.2.0 | Hudi 0.15.0"
echo "========================================================"

# ── Apache Iceberg ────────────────────────────────────────
export PYSPARK_SUBMIT_ARGS="\
--packages org.apache.iceberg:iceberg-spark-runtime-3.5_2.12:1.5.2 \
--conf spark.sql.extensions=org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions \
--conf spark.sql.catalog.local=org.apache.iceberg.spark.SparkCatalog \
--conf spark.sql.catalog.local.type=hadoop \
--conf spark.sql.catalog.local.warehouse=/app/warehouse/iceberg \
pyspark-shell"
python main.py --formats iceberg "$@"

# ── Delta Lake ────────────────────────────────────────────
export PYSPARK_SUBMIT_ARGS="\
--packages io.delta:delta-spark_2.12:3.2.0 \
--conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension \
--conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog \
pyspark-shell"
python main.py --formats delta "$@"

# ── Apache Hudi ───────────────────────────────────────────
export PYSPARK_SUBMIT_ARGS="\
--packages org.apache.hudi:hudi-spark3.5-bundle_2.12:0.15.0 \
--conf spark.sql.extensions=org.apache.spark.sql.hudi.HoodieSparkSessionExtension \
--conf spark.serializer=org.apache.spark.serializer.KryoSerializer \
pyspark-shell"
python main.py --formats hudi "$@"

echo ""
echo "All formats complete. Results in $RESULTS"

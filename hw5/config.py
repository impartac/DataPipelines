"""Configuration for Spark performance benchmarking."""

# Spark configuration
SPARK_CONFIG = {
    "spark.app.name": "DataFrame vs RDD Performance Benchmark",
    "spark.master": "local[*]",
    "spark.sql.shuffle.partitions": "8",
    "spark.default.parallelism": "8",
    "spark.driver.memory": "4g",
    "spark.executor.memory": "4g",
}

# Dataset sizes
DATASET_SIZES = {
    "small": 10_000,
    "medium": 100_000,
    "large": 1_000_000,
}

# Number of benchmark iterations
BENCHMARK_ITERATIONS = 3

# Test cases to run
TEST_CASES = [
    "multiple_aggregations",
    "window_functions",
    "nested_types",
    "conditional_logic",
    "sql_vs_dataframe_1",
    "sql_vs_dataframe_2",
]

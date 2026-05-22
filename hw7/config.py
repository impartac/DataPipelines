import os as _os

_HW7_DIR     = _os.path.dirname(_os.path.abspath(__file__))
WAREHOUSE_DIR = _os.path.join(_HW7_DIR, "warehouse")
RESULTS_DIR   = _os.path.join(_HW7_DIR, "results")

ICEBERG_WAREHOUSE = _os.path.join(WAREHOUSE_DIR, "iceberg")
DELTA_WAREHOUSE   = _os.path.join(WAREHOUSE_DIR, "delta")
HUDI_WAREHOUSE    = _os.path.join(WAREHOUSE_DIR, "hudi")

BASE_ROWS            = 10_000
FRACTIONS            = [0.5, 1.0]
BENCHMARK_ITERATIONS = 1
N_CONCURRENT_WRITERS = 4

_COMMON = {
    "spark.master":                 "local[*]",
    "spark.driver.memory":          "4g",
    "spark.executor.memory":        "4g",
    "spark.sql.shuffle.partitions": "8",
    "spark.default.parallelism":    "8",
    "spark.driver.host":            "localhost",
    "spark.driver.bindAddress":     "127.0.0.1",
    "spark.ui.enabled":             "false",
}

SPARK_CONFIGS = {
    "iceberg": {
        **_COMMON,
        "spark.app.name": "hw7-iceberg",
    },
    "delta": {
        **_COMMON,
        "spark.app.name": "hw7-delta",
    },
    "hudi": {
        **_COMMON,
        "spark.app.name": "hw7-hudi",
        "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
    },
}

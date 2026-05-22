TRINO_HOST = "localhost"
TRINO_PORT = 8080
TRINO_USER = "benchmark"
TRINO_CATALOG = "tpch"
TRINO_SCHEMA = "sf1"

STARROCKS_HOST = "localhost"
STARROCKS_PORT = 9030
STARROCKS_USER = "root"
STARROCKS_PASSWORD = ""
STARROCKS_DATABASE = "tpch_sf1"

TPCH_SCALE_FACTOR = 1
BENCHMARK_ITERATIONS = 3
QUERY_TIMEOUT_SECONDS = 300

DEFAULT_QUERY_IDS = [1, 3, 4, 5, 6, 7, 9, 12, 14, 17, 18, 21]

import os as _os
_HW9_DIR = _os.path.dirname(_os.path.abspath(__file__))
DATA_DIR = _os.path.join(_HW9_DIR, "data")
RESULTS_DIR = _os.path.join(_HW9_DIR, "results")

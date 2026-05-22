import random
from datetime import date, timedelta

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    DateType,
    FloatType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

SCHEMA = StructType([
    StructField("doc_id",       IntegerType(), False),
    StructField("category",     StringType(),  False),
    StructField("status",       StringType(),  False),
    StructField("amount",       FloatType(),   False),
    StructField("created_date", DateType(),    False),
    StructField("region",       StringType(),  False),
])

_CATEGORIES = ["LAW", "DECREE", "ORDER", "RESOLUTION", "LETTER"]
_STATUSES   = ["active", "amended", "cancelled", "draft"]
_REGIONS    = ["MSK", "SPB", "NSK", "EKB", "KZN"]
_BASE_DATE  = date(2020, 1, 1)


def generate_dataframe(spark: SparkSession, n_rows: int, id_offset: int = 0):
    rng = random.Random(n_rows + id_offset)
    rows = [
        (
            id_offset + i,
            rng.choice(_CATEGORIES),
            rng.choice(_STATUSES),
            round(rng.uniform(1.0, 1_000_000.0), 2),
            _BASE_DATE + timedelta(days=rng.randint(0, 1826)),
            rng.choice(_REGIONS),
        )
        for i in range(n_rows)
    ]
    return spark.createDataFrame(rows, SCHEMA)

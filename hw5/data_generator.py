"""Data generator for Spark benchmarking."""

import random
from datetime import datetime, timedelta
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, 
    FloatType, ArrayType, TimestampType
)


def generate_test_data(spark: SparkSession, num_rows: int):
    """Generate test dataset for benchmarking.
    
    Args:
        spark: SparkSession instance
        num_rows: Number of rows to generate
        
    Returns:
        DataFrame with test data
    """
    # Define schema
    schema = StructType([
        StructField("id", IntegerType(), False),
        StructField("category", StringType(), False),
        StructField("value", FloatType(), False),
        StructField("quantity", IntegerType(), False),
        StructField("timestamp", TimestampType(), False),
        StructField("tags", ArrayType(StringType()), True),
        StructField("metadata", StringType(), True),
    ])
    
    # Generate data
    categories = ["A", "B", "C", "D", "E"]
    tags_pool = ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"]
    base_date = datetime(2024, 1, 1)
    
    data = []
    for i in range(num_rows):
        row = (
            i,
            random.choice(categories),
            random.uniform(10.0, 1000.0),
            random.randint(1, 100),
            base_date + timedelta(days=random.randint(0, 365)),
            random.sample(tags_pool, k=random.randint(1, 4)),
            f'{{"user_id": {random.randint(1, 1000)}, "region": "{random.choice(["US", "EU", "ASIA"])}"}}',
        )
        data.append(row)
    
    return spark.createDataFrame(data, schema)


def generate_sales_data(spark: SparkSession, num_rows: int):
    """Generate sales dataset for SQL vs DataFrame comparison.
    
    Args:
        spark: SparkSession instance
        num_rows: Number of rows to generate
        
    Returns:
        DataFrame with sales data
    """
    schema = StructType([
        StructField("order_id", IntegerType(), False),
        StructField("customer_id", IntegerType(), False),
        StructField("product_id", IntegerType(), False),
        StructField("product_name", StringType(), False),
        StructField("amount", FloatType(), False),
        StructField("date", TimestampType(), False),
        StructField("status", StringType(), False),
    ])
    
    products = [
        "Laptop", "Phone", "Tablet", "Monitor", "Keyboard", 
        "Mouse", "Headphones", "Camera", "Printer", "Router"
    ]
    statuses = ["pending", "completed", "cancelled", "shipped"]
    base_date = datetime(2024, 1, 1)
    
    data = []
    for i in range(num_rows):
        row = (
            i,
            random.randint(1, num_rows // 10),  # ~10 orders per customer
            random.randint(1, len(products)),
            random.choice(products),
            random.uniform(50.0, 5000.0),
            base_date + timedelta(days=random.randint(0, 365)),
            random.choice(statuses),
        )
        data.append(row)
    
    return spark.createDataFrame(data, schema)

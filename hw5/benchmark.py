"""Performance benchmarks comparing DataFrame, RDD, and SQL APIs."""

import time
import json
from typing import Callable, Dict, List, Tuple, Optional
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, sum as spark_sum, avg, min as spark_min, max as spark_max,
    count, when, lit, row_number, explode, from_json, struct, array
)
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from pyspark.sql.window import Window

from config import BENCHMARK_ITERATIONS
from data_generator import generate_test_data, generate_sales_data


class BenchmarkResult:
    """Container for benchmark results."""
    
    def __init__(self, name: str, approach: str, execution_time: float, 
                 row_count: Optional[int] = None, additional_info: str = ""):
        self.name = name
        self.approach = approach
        self.execution_time = execution_time
        self.row_count = row_count
        self.additional_info = additional_info
    
    def to_dict(self):
        return {
            "name": self.name,
            "approach": self.approach,
            "execution_time": self.execution_time,
            "row_count": self.row_count,
            "additional_info": self.additional_info
        }


def time_execution(func: Callable, iterations: int = BENCHMARK_ITERATIONS) -> float:
    """Time the execution of a function over multiple iterations.
    
    Args:
        func: Function to benchmark
        iterations: Number of iterations to run
        
    Returns:
        Average execution time in seconds
    """
    times = []
    
    # Warm-up run
    func()
    
    for _ in range(iterations):
        start = time.time()
        func()
        end = time.time()
        times.append(end - start)
    
    return sum(times) / len(times)


class SparkBenchmarks:
    """Collection of Spark performance benchmarks."""
    
    def __init__(self, spark: SparkSession):
        self.spark = spark
        self.results: List[BenchmarkResult] = []
    
    def run_all(self, dataset_size: int) -> List[BenchmarkResult]:
        """Run all benchmarks.
        
        Args:
            dataset_size: Number of rows in test dataset
            
        Returns:
            List of benchmark results
        """
        print(f"\n{'='*80}")
        print(f"Running benchmarks with dataset size: {dataset_size:,} rows")
        print(f"{'='*80}\n")
        
        self.results = []
        
        # Case 1: Multiple Aggregations
        print("Case 1: Multiple Aggregations (DataFrame vs RDD)...")
        self.benchmark_multiple_aggregations(dataset_size)
        
        # Case 2: Window Functions
        print("Case 2: Window Functions (DataFrame vs RDD)...")
        self.benchmark_window_functions(dataset_size)
        
        # Case 3: Nested Types
        print("Case 3: Nested Types (DataFrame vs RDD)...")
        self.benchmark_nested_types(dataset_size)
        
        # Case 4: Conditional Logic
        print("Case 4: Conditional Logic (DataFrame vs RDD)...")
        self.benchmark_conditional_logic(dataset_size)
        
        # Case 5: SQL vs DataFrame - Complex Join
        print("Case 5: SQL vs DataFrame API - Complex Aggregation...")
        self.benchmark_sql_vs_dataframe_1(dataset_size)
        
        # Case 6: SQL vs DataFrame - Subquery
        print("Case 6: SQL vs DataFrame API - Correlated Subquery...")
        self.benchmark_sql_vs_dataframe_2(dataset_size)
        
        return self.results
    
    def benchmark_multiple_aggregations(self, dataset_size: int):
        """Benchmark: Multiple aggregations on grouped data.
        
        Catalyst optimization: Single-pass aggregation with code generation.
        Tungsten: Efficient memory layout for aggregation buffers.
        """
        df = generate_test_data(self.spark, dataset_size)
        df.cache()
        df.count()  # Materialize cache
        
        # DataFrame approach - single pass with multiple aggregations
        def dataframe_approach():
            result = df.groupBy("category").agg(
                spark_sum("value").alias("total"),
                avg("value").alias("average"),
                spark_min("value").alias("minimum"),
                spark_max("value").alias("maximum"),
                count("*").alias("count")
            )
            result.collect()
        
        # RDD approach - multiple passes
        def rdd_approach():
            rdd = df.rdd.map(lambda row: (row.category, row.value))
            
            # Each aggregation requires a separate action
            total = rdd.reduceByKey(lambda a, b: a + b).collect()
            
            # For average, need sum and count
            sum_count = rdd.aggregateByKey(
                (0.0, 0),
                lambda acc, v: (acc[0] + v, acc[1] + 1),
                lambda acc1, acc2: (acc1[0] + acc2[0], acc1[1] + acc2[1])
            )
            average = sum_count.mapValues(lambda x: x[0] / x[1] if x[1] > 0 else 0).collect()
            
            # Min and max
            minimum = rdd.reduceByKey(lambda a, b: min(a, b)).collect()
            maximum = rdd.reduceByKey(lambda a, b: max(a, b)).collect()
            count_vals = rdd.countByKey()
        
        df_time = time_execution(dataframe_approach)
        rdd_time = time_execution(rdd_approach)
        
        self.results.append(BenchmarkResult(
            "Multiple Aggregations", "DataFrame", df_time, dataset_size,
            "Single-pass aggregation with Catalyst optimization"
        ))
        self.results.append(BenchmarkResult(
            "Multiple Aggregations", "RDD", rdd_time, dataset_size,
            "Multiple passes over data"
        ))
        
        speedup = rdd_time / df_time
        print(f"  DataFrame: {df_time:.4f}s")
        print(f"  RDD: {rdd_time:.4f}s")
        print(f"  Speedup: {speedup:.2f}x\n")
        
        df.unpersist()
    
    def benchmark_window_functions(self, dataset_size: int):
        """Benchmark: Top-N per group using window functions.
        
        Catalyst optimization: Optimized window operator with partition pruning.
        Tungsten: Efficient in-memory sorting within partitions.
        """
        df = generate_test_data(self.spark, dataset_size)
        df.cache()
        df.count()
        
        TOP_N = 3
        
        # DataFrame approach with window functions
        def dataframe_approach():
            window_spec = Window.partitionBy("category").orderBy(col("value").desc())
            result = df.withColumn("rank", row_number().over(window_spec)) \
                      .filter(col("rank") <= TOP_N) \
                      .drop("rank")
            result.collect()
        
        # RDD approach - manual sorting and filtering
        def rdd_approach():
            rdd = df.rdd.map(lambda row: (row.category, row))
            
            # Group by category
            grouped = rdd.groupByKey()
            
            # Sort and take top N for each group
            def get_top_n(records):
                sorted_records = sorted(records, key=lambda r: r.value, reverse=True)
                return sorted_records[:TOP_N]
            
            result = grouped.flatMapValues(get_top_n).map(lambda x: x[1])
            result.collect()
        
        df_time = time_execution(dataframe_approach)
        rdd_time = time_execution(rdd_approach)
        
        self.results.append(BenchmarkResult(
            "Window Functions", "DataFrame", df_time, dataset_size,
            "Optimized window operator with partition-local sorting"
        ))
        self.results.append(BenchmarkResult(
            "Window Functions", "RDD", rdd_time, dataset_size,
            "Full groupByKey + local sorting"
        ))
        
        speedup = rdd_time / df_time
        print(f"  DataFrame: {df_time:.4f}s")
        print(f"  RDD: {rdd_time:.4f}s")
        print(f"  Speedup: {speedup:.2f}x\n")
        
        df.unpersist()
    
    def benchmark_nested_types(self, dataset_size: int):
        """Benchmark: Working with nested structures (arrays, JSON).
        
        Catalyst optimization: Native support for complex types without serialization.
        Tungsten: Binary format for nested structures, no JSON parsing overhead.
        """
        df = generate_test_data(self.spark, dataset_size)
        df.cache()
        df.count()
        
        # DataFrame approach - native array operations
        def dataframe_approach():
            # Explode array and work with structured data
            result = df.select("id", "category", explode("tags").alias("tag")) \
                      .groupBy("category", "tag") \
                      .count()
            result.collect()
        
        # RDD approach - manual parsing and processing
        def rdd_approach():
            rdd = df.rdd
            
            # Manually explode tags
            exploded = rdd.flatMap(
                lambda row: [(row.category, tag) for tag in (row.tags or [])]
            )
            
            # Count by key
            result = exploded.map(lambda x: (x, 1)) \
                            .reduceByKey(lambda a, b: a + b)
            result.collect()
        
        df_time = time_execution(dataframe_approach)
        rdd_time = time_execution(rdd_approach)
        
        self.results.append(BenchmarkResult(
            "Nested Types", "DataFrame", df_time, dataset_size,
            "Native complex type support, no serialization"
        ))
        self.results.append(BenchmarkResult(
            "Nested Types", "RDD", rdd_time, dataset_size,
            "Manual serialization/deserialization"
        ))
        
        speedup = rdd_time / df_time
        print(f"  DataFrame: {df_time:.4f}s")
        print(f"  RDD: {rdd_time:.4f}s")
        print(f"  Speedup: {speedup:.2f}x\n")
        
        df.unpersist()
    
    def benchmark_conditional_logic(self, dataset_size: int):
        """Benchmark: Complex conditional logic.
        
        Catalyst optimization: Predicate pushdown and expression optimization.
        Tungsten: Code generation for conditional expressions.
        """
        df = generate_test_data(self.spark, dataset_size)
        df.cache()
        df.count()
        
        # DataFrame approach - when/otherwise
        def dataframe_approach():
            result = df.withColumn(
                "category_tier",
                when(col("value") >= 800, "Premium")
                .when(col("value") >= 500, "Standard")
                .when(col("value") >= 200, "Basic")
                .otherwise("Economy")
            ).withColumn(
                "quantity_level",
                when(col("quantity") >= 75, "High")
                .when(col("quantity") >= 50, "Medium")
                .otherwise("Low")
            ).groupBy("category_tier", "quantity_level").count()
            
            result.collect()
        
        # RDD approach - multiple filters and unions
        def rdd_approach():
            rdd = df.rdd
            
            # Create separate RDDs for each condition
            premium = rdd.filter(lambda r: r.value >= 800).map(
                lambda r: (("Premium", "High" if r.quantity >= 75 else "Medium" if r.quantity >= 50 else "Low"), 1)
            )
            standard = rdd.filter(lambda r: 500 <= r.value < 800).map(
                lambda r: (("Standard", "High" if r.quantity >= 75 else "Medium" if r.quantity >= 50 else "Low"), 1)
            )
            basic = rdd.filter(lambda r: 200 <= r.value < 500).map(
                lambda r: (("Basic", "High" if r.quantity >= 75 else "Medium" if r.quantity >= 50 else "Low"), 1)
            )
            economy = rdd.filter(lambda r: r.value < 200).map(
                lambda r: (("Economy", "High" if r.quantity >= 75 else "Medium" if r.quantity >= 50 else "Low"), 1)
            )
            
            # Union and aggregate
            result = premium.union(standard).union(basic).union(economy) \
                           .reduceByKey(lambda a, b: a + b)
            result.collect()
        
        df_time = time_execution(dataframe_approach)
        rdd_time = time_execution(rdd_approach)
        
        self.results.append(BenchmarkResult(
            "Conditional Logic", "DataFrame", df_time, dataset_size,
            "Code generation for branching logic"
        ))
        self.results.append(BenchmarkResult(
            "Conditional Logic", "RDD", rdd_time, dataset_size,
            "Multiple scans with filter + union"
        ))
        
        speedup = rdd_time / df_time
        print(f"  DataFrame: {df_time:.4f}s")
        print(f"  RDD: {rdd_time:.4f}s")
        print(f"  Speedup: {speedup:.2f}x\n")
        
        df.unpersist()
    
    def benchmark_sql_vs_dataframe_1(self, dataset_size: int):
        """Benchmark: SQL vs DataFrame API - Complex aggregation with join.
        
        SQL may optimize better due to:
        - More aggressive predicate pushdown
        - Better join reordering
        - Cost-based optimization (CBO)
        """
        df = generate_sales_data(self.spark, dataset_size)
        df.createOrReplaceTempView("sales")
        df.cache()
        df.count()
        
        # SQL approach
        def sql_approach():
            query = """
                SELECT 
                    customer_id,
                    COUNT(*) as order_count,
                    SUM(amount) as total_spent,
                    AVG(amount) as avg_order,
                    MAX(amount) as max_order
                FROM sales
                WHERE status = 'completed'
                GROUP BY customer_id
                HAVING SUM(amount) > 1000
                ORDER BY total_spent DESC
                LIMIT 100
            """
            result = self.spark.sql(query)
            result.collect()
        
        # DataFrame API approach
        def dataframe_approach():
            result = df.filter(col("status") == "completed") \
                      .groupBy("customer_id") \
                      .agg(
                          count("*").alias("order_count"),
                          spark_sum("amount").alias("total_spent"),
                          avg("amount").alias("avg_order"),
                          spark_max("amount").alias("max_order")
                      ) \
                      .filter(col("total_spent") > 1000) \
                      .orderBy(col("total_spent").desc()) \
                      .limit(100)
            result.collect()
        
        sql_time = time_execution(sql_approach)
        df_time = time_execution(dataframe_approach)
        
        self.results.append(BenchmarkResult(
            "SQL vs DataFrame - Aggregation", "SQL", sql_time, dataset_size,
            "Query optimization with CBO"
        ))
        self.results.append(BenchmarkResult(
            "SQL vs DataFrame - Aggregation", "DataFrame API", df_time, dataset_size,
            "Programmatic API"
        ))
        
        difference = abs(sql_time - df_time)
        faster = "SQL" if sql_time < df_time else "DataFrame API"
        print(f"  SQL: {sql_time:.4f}s")
        print(f"  DataFrame API: {df_time:.4f}s")
        print(f"  Faster: {faster} by {difference:.4f}s\n")
        
        # Print execution plans
        print("  SQL Execution Plan:")
        sql_result = self.spark.sql("""
            SELECT customer_id, COUNT(*) as order_count, SUM(amount) as total_spent,
                   AVG(amount) as avg_order, MAX(amount) as max_order
            FROM sales
            WHERE status = 'completed'
            GROUP BY customer_id
            HAVING SUM(amount) > 1000
            ORDER BY total_spent DESC
            LIMIT 100
        """)
        sql_result.explain(extended=False)
        
        print("\n  DataFrame API Execution Plan:")
        df_result = df.filter(col("status") == "completed") \
                     .groupBy("customer_id") \
                     .agg(count("*").alias("order_count"),
                          spark_sum("amount").alias("total_spent"),
                          avg("amount").alias("avg_order"),
                          spark_max("amount").alias("max_order")) \
                     .filter(col("total_spent") > 1000) \
                     .orderBy(col("total_spent").desc()) \
                     .limit(100)
        df_result.explain(extended=False)
        print()
        
        df.unpersist()
    
    def benchmark_sql_vs_dataframe_2(self, dataset_size: int):
        """Benchmark: SQL vs DataFrame API - Subquery pattern.
        
        SQL may handle correlated subqueries more efficiently through:
        - Subquery decorrelation
        - Better predicate pushdown
        """
        df = generate_sales_data(self.spark, dataset_size)
        df.createOrReplaceTempView("sales")
        df.cache()
        df.count()
        
        # SQL approach with subquery
        def sql_approach():
            query = """
                SELECT s1.customer_id, s1.product_name, s1.amount
                FROM sales s1
                WHERE s1.amount > (
                    SELECT AVG(s2.amount)
                    FROM sales s2
                    WHERE s2.customer_id = s1.customer_id
                )
                AND s1.status = 'completed'
            """
            result = self.spark.sql(query)
            result.collect()
        
        # DataFrame API approach (simulating the subquery)
        def dataframe_approach():
            # Calculate average per customer
            avg_per_customer = df.filter(col("status") == "completed") \
                                .groupBy("customer_id") \
                                .agg(avg("amount").alias("avg_amount"))
            
            # Join back and filter
            result = df.filter(col("status") == "completed") \
                      .alias("s1") \
                      .join(avg_per_customer.alias("avg"), "customer_id") \
                      .filter(col("s1.amount") > col("avg_amount")) \
                      .select("s1.customer_id", "s1.product_name", "s1.amount")
            result.collect()
        
        sql_time = time_execution(sql_approach)
        df_time = time_execution(dataframe_approach)
        
        self.results.append(BenchmarkResult(
            "SQL vs DataFrame - Subquery", "SQL", sql_time, dataset_size,
            "Subquery decorrelation optimization"
        ))
        self.results.append(BenchmarkResult(
            "SQL vs DataFrame - Subquery", "DataFrame API", df_time, dataset_size,
            "Manual join pattern"
        ))
        
        difference = abs(sql_time - df_time)
        faster = "SQL" if sql_time < df_time else "DataFrame API"
        print(f"  SQL: {sql_time:.4f}s")
        print(f"  DataFrame API: {df_time:.4f}s")
        print(f"  Faster: {faster} by {difference:.4f}s\n")
        
        # Print execution plans
        print("  SQL Execution Plan:")
        sql_result = self.spark.sql("""
            SELECT s1.customer_id, s1.product_name, s1.amount
            FROM sales s1
            WHERE s1.amount > (
                SELECT AVG(s2.amount)
                FROM sales s2
                WHERE s2.customer_id = s1.customer_id
            )
            AND s1.status = 'completed'
        """)
        sql_result.explain(extended=False)
        
        print("\n  DataFrame API Execution Plan:")
        avg_per_customer = df.filter(col("status") == "completed") \
                            .groupBy("customer_id") \
                            .agg(avg("amount").alias("avg_amount"))
        df_result = df.filter(col("status") == "completed") \
                     .alias("s1") \
                     .join(avg_per_customer.alias("avg"), "customer_id") \
                     .filter(col("s1.amount") > col("avg_amount")) \
                     .select("s1.customer_id", "s1.product_name", "s1.amount")
        df_result.explain(extended=False)
        print()
        
        df.unpersist()


def get_benchmark_summary(results: List[BenchmarkResult]) -> Dict:
    """Generate summary statistics from benchmark results.
    
    Args:
        results: List of benchmark results
        
    Returns:
        Dictionary with summary statistics
    """
    summary = {}
    
    # Group by test case
    by_case = {}
    for result in results:
        if result.name not in by_case:
            by_case[result.name] = []
        by_case[result.name].append(result)
    
    # Calculate speedups
    for case_name, case_results in by_case.items():
        if len(case_results) == 2:
            df_time = next(r.execution_time for r in case_results if "DataFrame" in r.approach or "SQL" in r.approach)
            rdd_time = next(r.execution_time for r in case_results if "RDD" in r.approach or ("DataFrame API" in r.approach and "SQL" in case_name))
            
            speedup = rdd_time / df_time if df_time > 0 else 0
            summary[case_name] = {
                "df_time": df_time,
                "rdd_time": rdd_time,
                "speedup": speedup
            }
    
    return summary

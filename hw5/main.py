"""Main script to run performance benchmarks."""

import sys
import os
from pyspark.sql import SparkSession

from config import SPARK_CONFIG, DATASET_SIZES
from benchmark import SparkBenchmarks
from report_generator import generate_markdown_report


def create_spark_session():
    """Create and configure Spark session."""
    builder = SparkSession.builder
    
    for key, value in SPARK_CONFIG.items():
        builder = builder.config(key, value)
    
    return builder.getOrCreate()


def main():
    """Run all benchmarks and generate report."""
    print("="*80)
    print("Apache Spark Performance Benchmark: DataFrame vs RDD vs SQL")
    print("="*80)
    
    # Get dataset size from command line or use default
    if len(sys.argv) > 1:
        size_name = sys.argv[1].lower()
        if size_name in DATASET_SIZES:
            dataset_size = DATASET_SIZES[size_name]
        else:
            print(f"Invalid size '{size_name}'. Using 'medium'.")
            print(f"Available sizes: {', '.join(DATASET_SIZES.keys())}")
            dataset_size = DATASET_SIZES["medium"]
    else:
        dataset_size = DATASET_SIZES["medium"]
    
    print(f"\nDataset size: {dataset_size:,} rows")
    
    # Create reports directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)
    
    # Create Spark session
    print("\nInitializing Spark session...")
    spark = create_spark_session()
    
    # Set log level to reduce noise
    spark.sparkContext.setLogLevel("WARN")
    
    try:
        # Run benchmarks
        benchmarks = SparkBenchmarks(spark)
        results = benchmarks.run_all(dataset_size)
        
        # Generate report
        output_file = f"reports/performance_report_{dataset_size}.md"
        generate_markdown_report(results, dataset_size, output_file)
        
        print("\n" + "="*80)
        print("Benchmark completed successfully!")
        print("="*80)
        
    except Exception as e:
        print(f"\nError during benchmark execution: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        spark.stop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

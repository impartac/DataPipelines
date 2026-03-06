"""Simple test to verify Spark installation."""

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as spark_sum, avg

def test_basic_spark():
    """Test basic Spark functionality."""
    print("Creating Spark session...")
    
    spark = SparkSession.builder \
        .appName("Simple Test") \
        .master("local[1]") \
        .config("spark.driver.memory", "2g") \
        .config("spark.sql.shuffle.partitions", "2") \
        .config("spark.python.worker.reuse", "false") \
        .getOrCreate()
    
    spark.sparkContext.setLogLevel("ERROR")
    
    try:
        print("Creating test DataFrame...")
        data = [
            (1, "A", 100.0),
            (2, "B", 200.0),
            (3, "A", 150.0),
            (4, "B", 250.0),
        ]
        
        df = spark.createDataFrame(data, ["id", "category", "value"])
        
        print("\nTest DataFrame:")
        df.show()
        
        print("\nPerforming aggregation...")
        result = df.groupBy("category").agg(
            spark_sum("value").alias("total"),
            avg("value").alias("average")
        )
        
        print("\nAggregation result:")
        result.show()
        
        print("\n✅ Basic Spark test passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        spark.stop()


if __name__ == "__main__":
    success = test_basic_spark()
    exit(0 if success else 1)

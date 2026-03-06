import config
from data_generator import EcommerceDataGenerator
from performance_tester import PerformanceTester


def main():
    
    print("=" * 80)
    print("DATA FORMAT PERFORMANCE COMPARISON")
    print("=" * 80)
    print(f"Target dataset size: ~{config.TARGET_SIZE_GB} GB")
    print(f"Estimated records: {config.NUM_RECORDS:,}")
    print()
    
    print("STEP 1: Generating E-commerce Orders Dataset")
    print("-" * 80)
    generator = EcommerceDataGenerator(seed=config.RANDOM_SEED)
    df = generator.generate_batch(config.NUM_RECORDS)
    
    actual_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    print(f"\nDataset generated successfully!")
    print(f"   Records: {len(df):,}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   Memory size: {actual_size_mb:.2f} MB (~{actual_size_mb/1024:.2f} GB)")
    print(f"\nDataset preview:")
    print(df.head())
    print(f"\nDataset info:")
    print(df.info())
    
    print("\n" + "=" * 80)
    print("STEP 2: Running Performance Tests")
    print("-" * 80)
    
    tester = PerformanceTester(output_dir=config.OUTPUT_DIR, test_type="full")
    tester.run_tests(df)
    
    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED!")
    print("=" * 80)


if __name__ == "__main__":
    main()

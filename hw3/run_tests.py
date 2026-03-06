import sys
import config
from data_generator import EcommerceDataGenerator
from performance_tester import PerformanceTester


def run_quick_test():
    print("Running QUICK TEST (1 million records)...")
    config.NUM_RECORDS = 1_000_000
    _run_test("quick")


def run_medium_test():
    print("Running MEDIUM TEST (5 million records)...")
    config.NUM_RECORDS = 5_000_000
    _run_test("medium")


def run_full_test():
    print("Running FULL TEST (~10GB dataset)...")
    config.NUM_RECORDS = int((config.TARGET_SIZE_GB * 1024 * 1024) / config.RECORD_SIZE_KB)
    _run_test("full")


def _run_test(test_type: str):
    generator = EcommerceDataGenerator(seed=config.RANDOM_SEED)
    df = generator.generate_batch(config.NUM_RECORDS)
    
    print(f"\nDataset generated: {len(df):,} records")
    print(f"   Memory: {df.memory_usage(deep=True).sum() / (1024**2):.2f} MB\n")
    
    tester = PerformanceTester(output_dir=config.OUTPUT_DIR, test_type=test_type)
    tester.run_tests(df)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        if test_type == "quick":
            run_quick_test()
        elif test_type == "medium":
            run_medium_test()
        elif test_type == "full":
            run_full_test()
        else:
            print(f"Unknown test type: {test_type}")
            print("Usage: python run_tests.py [quick|medium|full]")
    else:
        print("Usage: python run_tests.py [quick|medium|full]")
        print("\nTest types:")
        print("  quick  - 1 million records (~100MB)")
        print("  medium - 5 million records (~500MB)")
        print("  full   - ~10GB dataset")

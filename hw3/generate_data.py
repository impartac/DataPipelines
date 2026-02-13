import sys
from typing import Optional
import config
from data_generator import EcommerceDataGenerator
from format_handlers import get_all_handlers


def generate_and_save(num_records: int, formats: Optional[list] = None):
    if formats is None:
        formats = ["Parquet", "Avro", "CSV", "JSON"]
    
    print(f"Generating dataset with {num_records:,} records...")
    generator = EcommerceDataGenerator(seed=config.RANDOM_SEED)
    df = generator.generate_batch(num_records)
    
    actual_size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    print(f"\nDataset generated: {len(df):,} records")
    print(f"   Memory: {actual_size_mb:.2f} MB (~{actual_size_mb/1024:.2f} GB)\n")
    
    handlers = get_all_handlers(config.OUTPUT_DIR)
    
    print("Saving to formats:")
    for format_name in formats:
        if format_name not in handlers:
            print(f"WARNING: Unknown format: {format_name}")
            continue
        
        handler = handlers[format_name]
        filename = f"orders.{format_name.lower()}"
        
        print(f"\n[{format_name}] Saving...")
        filepath = handler.write(df, filename)
        size_mb = handler.get_file_size_mb(filepath)
        print(f"[{format_name}] Saved: {filepath}")
        print(f"[{format_name}] Size: {size_mb:.2f} MB")
    
    print(f"\nAll files saved to: {config.OUTPUT_DIR}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            num_records = int(sys.argv[1])
            formats = sys.argv[2:] if len(sys.argv) > 2 else None
            
            if formats:
                formats = [f.capitalize() for f in formats]
                print(f"Selected formats: {', '.join(formats)}")
            
            generate_and_save(num_records, formats)
            
        except ValueError:
            print("Error: First argument must be a number")
            print("Usage: python generate_data.py <num_records> [format1 format2 ...]")
            print("Example: python generate_data.py 1000000 parquet csv")
    else:
        print("Usage: python generate_data.py <num_records> [format1 format2 ...]")
        print("\nExamples:")
        print("  python generate_data.py 1000000              # All formats")
        print("  python generate_data.py 5000000 parquet      # Only Parquet")
        print("  python generate_data.py 100000 parquet csv   # Parquet and CSV")
        print("\nAvailable formats: parquet, avro, csv, json")

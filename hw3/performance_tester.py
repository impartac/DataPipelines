import os
import time
from typing import Callable
import pandas as pd
from datetime import datetime
from format_handlers import get_all_handlers


class PerformanceTester:
    
    def __init__(self, output_dir: str, test_type: str = "general"):
        self.output_dir = output_dir
        self.test_type = test_type
        os.makedirs(output_dir, exist_ok=True)
        
        self.handlers = get_all_handlers(output_dir)
        
        self.results = {
            "format": [],
            "storage_mb": [],
            "write_time_sec": [],
            "read_full_time_sec": [],
            "read_sample_time_sec": [],
            "aggregation_time_sec": [],
        }
    
    def measure_time(self, func: Callable, *args, **kwargs) -> tuple:
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        return result, elapsed_time
    
    def test_write(self, format_name: str, df: pd.DataFrame, filename: str) -> tuple:
        print(f"\n[{format_name}] Writing data...")
        handler = self.handlers[format_name]
        filepath, write_time = self.measure_time(handler.write, df, filename)
        file_size_mb = handler.get_file_size_mb(filepath)
        print(f"[{format_name}] Write completed: {write_time:.2f}s, Size: {file_size_mb:.2f} MB")
        return filepath, write_time, file_size_mb
    
    def test_read_full(self, format_name: str, filepath: str) -> tuple:
        print(f"[{format_name}] Reading full dataset...")
        handler = self.handlers[format_name]
        df, read_time = self.measure_time(handler.read_full, filepath)
        print(f"[{format_name}] Full read completed: {read_time:.2f}s, Records: {len(df):,}")
        return df, read_time
    
    def test_read_sample(self, format_name: str, filepath: str) -> tuple:
        print(f"[{format_name}] Reading sample (filtered)...")
        handler = self.handlers[format_name]
        
        if format_name == "Parquet":
            df, read_time = self.measure_time(
                handler.read_filtered, 
                filepath, 
                filters=[('product_category', '=', 'Electronics')]
            )
        else:
            df_full, read_time = self.measure_time(handler.read_full, filepath)
            df = df_full[df_full['product_category'] == 'Electronics']
        
        print(f"[{format_name}] Sample read completed: {read_time:.2f}s, Records: {len(df):,}")
        return df, read_time
    
    def test_aggregation(self, format_name: str, filepath: str) -> tuple:
        print(f"[{format_name}] Running aggregation...")
        handler = self.handlers[format_name]
        
        def aggregate():
            if format_name == "Parquet":
                df = handler.read_columns(filepath, ['product_category', 'total_price', 'quantity', 'order_id'])
            else:
                df = handler.read_full(filepath)
            
            result = df.groupby('product_category').agg({
                'total_price': 'sum',
                'quantity': 'sum',
                'order_id': 'count'
            })
            return result
        
        result, agg_time = self.measure_time(aggregate)
        print(f"[{format_name}] Aggregation completed: {agg_time:.2f}s")
        return result, agg_time
    
    def run_tests(self, df: pd.DataFrame):
        print("=" * 80)
        print("PERFORMANCE TESTING - E-COMMERCE ORDERS DATASET")
        print("=" * 80)
        print(f"Dataset size: {len(df):,} records")
        print(f"Memory usage: {df.memory_usage(deep=True).sum() / (1024**2):.2f} MB")
        print()
        
        for format_name in self.handlers.keys():
            print("=" * 80)
            print(f"Testing format: {format_name}")
            print("=" * 80)
            
            filename = f"orders.{format_name.lower()}"
            
            try:
                filepath, write_time, file_size_mb = self.test_write(format_name, df, filename)
                
                df_read, read_full_time = self.test_read_full(format_name, filepath)
                
                _, read_sample_time = self.test_read_sample(format_name, filepath)
                
                _, agg_time = self.test_aggregation(format_name, filepath)
                
                self.results["format"].append(format_name)
                self.results["storage_mb"].append(file_size_mb)
                self.results["write_time_sec"].append(write_time)
                self.results["read_full_time_sec"].append(read_full_time)
                self.results["read_sample_time_sec"].append(read_sample_time)
                self.results["aggregation_time_sec"].append(agg_time)
                
            except Exception as e:
                print(f"[{format_name}] ERROR: {str(e)}")
                import traceback
                traceback.print_exc()
        
        self._print_summary()
        self._save_results()
        self._generate_md_report(df)
    
    def _print_summary(self):
        print("\n" + "=" * 80)
        print("PERFORMANCE SUMMARY")
        print("=" * 80)
        
        results_df = pd.DataFrame(self.results)
        
        print("\nSTORAGE SIZE (MB):")
        print(results_df[["format", "storage_mb"]].to_string(index=False))
        
        print("\nWRITE TIME (seconds):")
        print(results_df[["format", "write_time_sec"]].to_string(index=False))
        
        print("\nREAD TIMES (seconds):")
        print(results_df[["format", "read_full_time_sec", "read_sample_time_sec", "aggregation_time_sec"]].to_string(index=False))
        
        print("\nRANKINGS:")
        print(f"  Smallest storage: {results_df.loc[results_df['storage_mb'].idxmin(), 'format']}")
        print(f"  Fastest write: {results_df.loc[results_df['write_time_sec'].idxmin(), 'format']}")
        print(f"  Fastest full read: {results_df.loc[results_df['read_full_time_sec'].idxmin(), 'format']}")
        print(f"  Fastest aggregation: {results_df.loc[results_df['aggregation_time_sec'].idxmin(), 'format']}")
    
    def _save_results(self):
        results_df = pd.DataFrame(self.results)
        results_path = "performance_results.csv"
        results_df.to_csv(results_path, index=False)
        print(f"\nResults saved to: {results_path}")
    
    def _generate_md_report(self, df: pd.DataFrame):
        results_df = pd.DataFrame(self.results)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_type_upper = self.test_type.upper()
        
        report_lines = []
        report_lines.append(f"# Performance Test Report - {test_type_upper}")
        report_lines.append(f"\nGenerated: {timestamp}")
        report_lines.append(f"\n## Test Configuration")
        report_lines.append(f"\n- Test Type: {test_type_upper}")
        report_lines.append(f"- Dataset Size: {len(df):,} records")
        report_lines.append(f"- Memory Usage: {df.memory_usage(deep=True).sum() / (1024**2):.2f} MB")
        report_lines.append(f"- Number of Columns: {len(df.columns)}")
        
        report_lines.append(f"\n## Results Summary")
        report_lines.append(f"\n### Full Results Table")
        report_lines.append("\n```")
        report_lines.append(results_df.to_string(index=False))
        report_lines.append("```")
        
        report_lines.append(f"\n## Detailed Analysis")
        
        report_lines.append(f"\n### 1. Storage Efficiency")
        report_lines.append("\n| Format | Size (MB) |")
        report_lines.append("| ------ | --------- |")
        storage_sorted = results_df.sort_values('storage_mb')
        for _, row in storage_sorted.iterrows():
            report_lines.append(f"| {row['format']} | {row['storage_mb']:.2f} |")
        
        report_lines.append(f"\n### 2. Write Performance")
        report_lines.append("\n| Format | Time (sec) |")
        report_lines.append("| ------ | ---------- |")
        write_sorted = results_df.sort_values('write_time_sec')
        for _, row in write_sorted.iterrows():
            report_lines.append(f"| {row['format']} | {row['write_time_sec']:.2f} |")
        
        report_lines.append(f"\n### 3. Read Performance (Full Scan)")
        report_lines.append("\n| Format | Time (sec) |")
        report_lines.append("| ------ | ---------- |")
        read_sorted = results_df.sort_values('read_full_time_sec')
        for _, row in read_sorted.iterrows():
            report_lines.append(f"| {row['format']} | {row['read_full_time_sec']:.2f} |")
        
        report_lines.append(f"\n### 4. Read Performance (Filtered)")
        report_lines.append("\n| Format | Time (sec) |")
        report_lines.append("| ------ | ---------- |")
        sample_sorted = results_df.sort_values('read_sample_time_sec')
        for _, row in sample_sorted.iterrows():
            report_lines.append(f"| {row['format']} | {row['read_sample_time_sec']:.2f} |")
        
        report_lines.append(f"\n### 5. Aggregation Performance")
        report_lines.append("\n| Format | Time (sec) |")
        report_lines.append("| ------ | ---------- |")
        agg_sorted = results_df.sort_values('aggregation_time_sec')
        for _, row in agg_sorted.iterrows():
            report_lines.append(f"| {row['format']} | {row['aggregation_time_sec']:.2f} |")
        
        report_lines.append(f"\n## Winners")
        report_lines.append(f"\n- **Best Storage**: {results_df.loc[results_df['storage_mb'].idxmin(), 'format']}")
        report_lines.append(f"- **Fastest Write**: {results_df.loc[results_df['write_time_sec'].idxmin(), 'format']}")
        report_lines.append(f"- **Fastest Read**: {results_df.loc[results_df['read_full_time_sec'].idxmin(), 'format']}")
        report_lines.append(f"- **Fastest Filter**: {results_df.loc[results_df['read_sample_time_sec'].idxmin(), 'format']}")
        report_lines.append(f"- **Fastest Aggregation**: {results_df.loc[results_df['aggregation_time_sec'].idxmin(), 'format']}")
        
        report_lines.append(f"\n## Relative Performance")
        report_lines.append("\nNormalized to best performance (1.00x = best):")
        report_lines.append("\n```")
        normalized_df = results_df.copy()
        normalized_df['storage_ratio'] = results_df['storage_mb'] / results_df['storage_mb'].min()
        normalized_df['write_ratio'] = results_df['write_time_sec'] / results_df['write_time_sec'].min()
        normalized_df['read_ratio'] = results_df['read_full_time_sec'] / results_df['read_full_time_sec'].min()
        normalized_df['agg_ratio'] = results_df['aggregation_time_sec'] / results_df['aggregation_time_sec'].min()
        
        report_lines.append("Format      Storage  Write   Read    Agg")
        report_lines.append("-" * 50)
        for _, row in normalized_df.iterrows():
            report_lines.append(f"{row['format']:10s}  {row['storage_ratio']:5.2f}x   {row['write_ratio']:5.2f}x  {row['read_ratio']:5.2f}x  {row['agg_ratio']:5.2f}x")
        report_lines.append("```")
        
        report_lines.append(f"\n## Conclusions")
        report_lines.append(f"\nBest format: **{results_df.loc[results_df['storage_mb'].idxmin(), 'format']}**")
        report_lines.append(f"\nKey insights:")
        parquet_row = results_df[results_df['format'] == 'Parquet'].iloc[0] if 'Parquet' in results_df['format'].values else None
        if parquet_row is not None:
            report_lines.append(f"- Parquet provides {results_df['storage_mb'].max() / parquet_row['storage_mb']:.1f}x better compression than worst format")
            report_lines.append(f"- Parquet read operations are {results_df['read_full_time_sec'].max() / parquet_row['read_full_time_sec']:.1f}x faster than slowest format")
        
        report_path = f"performance_report_{self.test_type}.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        print(f"MD report saved to: {report_path}")

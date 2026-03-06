import os
from typing import List
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from fastavro import writer, reader, parse_schema
import config


class FormatHandler:
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    def get_file_size(self, filepath: str) -> int:
        if os.path.exists(filepath):
            return os.path.getsize(filepath)
        return 0
    
    def get_file_size_mb(self, filepath: str) -> float:
        return self.get_file_size(filepath) / (1024 * 1024)


class ParquetHandler(FormatHandler):
    
    def write(self, df: pd.DataFrame, filename: str) -> str:
        filepath = os.path.join(self.base_path, filename)
        table = pa.Table.from_pandas(df)
        pq.write_table(table, filepath, compression='snappy')
        return filepath
    
    def read_full(self, filepath: str) -> pd.DataFrame:
        return pd.read_parquet(filepath)
    
    def read_filtered(self, filepath: str, filters=None) -> pd.DataFrame:
        return pd.read_parquet(filepath, filters=filters)
    
    def read_columns(self, filepath: str, columns: List[str]) -> pd.DataFrame:
        return pd.read_parquet(filepath, columns=columns)


class AvroHandler(FormatHandler):
    
    def write(self, df: pd.DataFrame, filename: str) -> str:
        filepath = os.path.join(self.base_path, filename)
        parsed_schema = parse_schema(config.AVRO_SCHEMA)
        
        records = []
        for _, row in df.iterrows():
            record = row.to_dict()
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif key == 'customer_rating' and value is not None:
                    record[key] = int(value)
            records.append(record)
        
        with open(filepath, 'wb') as out:
            writer(out, parsed_schema, records)
        
        return filepath
    
    def read_full(self, filepath: str) -> pd.DataFrame:
        records = []
        with open(filepath, 'rb') as fo:
            avro_reader = reader(fo)
            for record in avro_reader:
                records.append(record)
        return pd.DataFrame(records)


class CSVHandler(FormatHandler):
    
    def write(self, df: pd.DataFrame, filename: str) -> str:
        filepath = os.path.join(self.base_path, filename)
        df.to_csv(filepath, index=False)
        return filepath
    
    def read_full(self, filepath: str) -> pd.DataFrame:
        return pd.read_csv(filepath)


class JSONHandler(FormatHandler):
    
    def write(self, df: pd.DataFrame, filename: str) -> str:
        filepath = os.path.join(self.base_path, filename)
        df.to_json(filepath, orient='records', lines=True)
        return filepath
    
    def read_full(self, filepath: str) -> pd.DataFrame:
        return pd.read_json(filepath, orient='records', lines=True)


def get_all_handlers(output_dir: str):
    return {
        "Parquet": ParquetHandler(os.path.join(output_dir, "parquet")),
        "Avro": AvroHandler(os.path.join(output_dir, "avro")),
        "CSV": CSVHandler(os.path.join(output_dir, "csv")),
        "JSON": JSONHandler(os.path.join(output_dir, "json")),
    }

# Performance Test Report - QUICK

Generated: 2026-02-10 21:56:35

## Test Configuration

- Test Type: QUICK
- Dataset Size: 10,000 records
- Memory Usage: 3.59 MB
- Number of Columns: 23

## Results Summary

### Full Results Table

```
 format  storage_mb  write_time_sec  read_full_time_sec  read_sample_time_sec  aggregation_time_sec
Parquet    1.359613        0.052737            0.068083              0.009508              0.007630
   Avro    2.408539        0.884662            0.131842              0.141542              0.151228
    CSV    2.330764        0.131031            0.093037              0.073289              0.074242
   JSON    5.886793        0.089261            0.141821              0.138897              0.134496
```

## Detailed Analysis

### 1. Storage Efficiency

| Format | Size (MB) |
| ------ | --------- |
| Parquet | 1.36 |
| CSV | 2.33 |
| Avro | 2.41 |
| JSON | 5.89 |

### 2. Write Performance

| Format | Time (sec) |
| ------ | ---------- |
| Parquet | 0.05 |
| JSON | 0.09 |
| CSV | 0.13 |
| Avro | 0.88 |

### 3. Read Performance (Full Scan)

| Format | Time (sec) |
| ------ | ---------- |
| Parquet | 0.07 |
| CSV | 0.09 |
| Avro | 0.13 |
| JSON | 0.14 |

### 4. Read Performance (Filtered)

| Format | Time (sec) |
| ------ | ---------- |
| Parquet | 0.01 |
| CSV | 0.07 |
| JSON | 0.14 |
| Avro | 0.14 |

### 5. Aggregation Performance

| Format | Time (sec) |
| ------ | ---------- |
| Parquet | 0.01 |
| CSV | 0.07 |
| JSON | 0.13 |
| Avro | 0.15 |

## Winners

- **Best Storage**: Parquet
- **Fastest Write**: Parquet
- **Fastest Read**: Parquet
- **Fastest Filter**: Parquet
- **Fastest Aggregation**: Parquet

## Relative Performance

Normalized to best performance (1.00x = best):

```
Format      Storage  Write   Read    Agg
--------------------------------------------------
Parquet      1.00x    1.00x   1.00x   1.00x
Avro         1.77x   16.77x   1.94x  19.82x
CSV          1.71x    2.48x   1.37x   9.73x
JSON         4.33x    1.69x   2.08x  17.63x
```

## Conclusions

Best format: **Parquet**

Key insights:
- Parquet provides 4.3x better compression than worst format
- Parquet read operations are 2.1x faster than slowest format
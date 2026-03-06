# Performance Test Report - MEDIUM

Generated: 2026-02-10 22:22:19

## Test Configuration

- Test Type: MEDIUM
- Dataset Size: 5,000,000 records
- Memory Usage: 1792.90 MB
- Number of Columns: 23

## Results Summary

### Full Results Table

```
 format  storage_mb  write_time_sec  read_full_time_sec  read_sample_time_sec  aggregation_time_sec
Parquet  544.726866        7.346445            0.806057              0.816348              0.478854
   Avro 1203.764163      470.970829           76.279509             82.792329             77.669017
    CSV 1165.335295       50.518383           31.418577             31.716914             31.805065
   JSON 2943.224570       45.868313           95.406096            116.884366            111.059706
```

## Detailed Analysis

### 1. Storage Efficiency

| Format | Size (MB) |
| ------ | --------- |
| Parquet | 544.73 |
| CSV | 1165.34 |
| Avro | 1203.76 |
| JSON | 2943.22 |

### 2. Write Performance

| Format | Time (sec) |
| ------ | ---------- |
| Parquet | 7.35 |
| JSON | 45.87 |
| CSV | 50.52 |
| Avro | 470.97 |

### 3. Read Performance (Full Scan)

| Format | Time (sec) |
| ------ | ---------- |
| Parquet | 0.81 |
| CSV | 31.42 |
| Avro | 76.28 |
| JSON | 95.41 |

### 4. Read Performance (Filtered)

| Format | Time (sec) |
| ------ | ---------- |
| Parquet | 0.82 |
| CSV | 31.72 |
| Avro | 82.79 |
| JSON | 116.88 |

### 5. Aggregation Performance

| Format | Time (sec) |
| ------ | ---------- |
| Parquet | 0.48 |
| CSV | 31.81 |
| Avro | 77.67 |
| JSON | 111.06 |

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
Avro         2.21x   64.11x  94.63x  162.20x
CSV          2.14x    6.88x  38.98x  66.42x
JSON         5.40x    6.24x  118.36x  231.93x
```

## Conclusions

Best format: **Parquet**

Key insights:
- Parquet provides 5.4x better compression than worst format
- Parquet read operations are 118.4x faster than slowest format
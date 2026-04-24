# Архитектура и диаграммы Workflow Templates

## 📐 Архитектурные диаграммы

### 1. Обзор всех шаблонов

```
┌─────────────────────────────────────────────────────────────────┐
│                    WORKFLOW TEMPLATES ECOSYSTEM                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌───────────────────┐    ┌────────────────────┐                │
│  │ Data Validation   │    │  ETL Processing    │                │
│  │   Template        │───▶│    Template        │                │
│  │                   │    │                    │                │
│  │ • Schema check    │    │ • Filter           │                │
│  │ • NULL check      │    │ • Aggregate        │                │
│  │ • Duplicates      │    │ • Join             │                │
│  └───────────────────┘    │ • Enrich           │                │
│           │                └────────────────────┘                │
│           │                         │                            │
│           ▼                         ▼                            │
│  ┌───────────────────┐    ┌────────────────────┐                │
│  │   Conditional     │    │  Batch File        │                │
│  │    Execution      │───▶│   Processor        │                │
│  │   Template        │    │   Template         │                │
│  │                   │    │                    │                │
│  │ • Threshold       │    │ • Analyze          │                │
│  │ • Status check    │    │ • Copy/Move        │                │
│  │ • Regex match     │    │ • Compress         │                │
│  └───────────────────┘    │ • Transform        │                │
│           │                └────────────────────┘                │
│           │                                                       │
│           ▼                                                       │
│  ┌───────────────────────────────────────────┐                  │
│  │      Notification Template                │                  │
│  │                                           │                  │
│  │  • Slack      • Teams                     │                  │
│  │  • Email      • Webhook                   │                  │
│  └───────────────────────────────────────────┘                  │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2. Основной Data Pipeline Workflow

```
START
  │
  ▼
┌─────────────────────────┐
│  Pipeline Start         │
│  Notification           │
│  (Slack/Email)          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Data Validation        │
│  Template               │
│                         │
│  Inputs:                │
│  • data-path            │
│  • validation-rules     │
│                         │
│  Outputs:               │
│  • validation-status    │
│  • error-count          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Check Validation       │
│  Status                 │
│  (Conditional Template) │
│                         │
│  condition == "success" │
└───────┬─────────┬───────┘
        │ YES     │ NO
        │         │
        ▼         └──────────────────┐
┌─────────────────────────┐          │
│  ETL Processing         │          │
│  Template               │          │
│                         │          │
│  Transformation:        │          │
│  • Filter data          │          │
│  • Convert format       │          │
│  • Add metadata         │          │
│                         │          │
│  Outputs:               │          │
│  • records-processed    │          │
│  • processing-time      │          │
└───────────┬─────────────┘          │
            │                        │
            ▼                        │
┌─────────────────────────┐          │
│  Quality Check          │          │
│  (Conditional Template) │          │
│                         │          │
│  records >= threshold?  │          │
└───────┬─────────┬───────┘          │
        │ YES     │ NO               │
        │         └──────────┐       │
        ▼                    │       │
┌─────────────────────────┐ │       │
│  Batch File Processing  │ │       │
│  Template               │ │       │
│                         │ │       │
│  Operations:            │ │       │
│  • Compress files       │ │       │
│  • Archive results      │ │       │
│                         │ │       │
│  Outputs:               │ │       │
│  • files-processed      │ │       │
│  • total-size           │ │       │
└───────────┬─────────────┘ │       │
            │               │       │
            ▼               ▼       ▼
      ┌──────────┐    ┌──────────┐
      │ Success  │    │ Failure  │
      │ Notify   │    │ Notify   │
      └────┬─────┘    └────┬─────┘
           │               │
           └───────┬───────┘
                   │
                   ▼
                  END
```

---

### 3. Детальная схема Data Validation Template

```
┌─────────────────────────────────────────────────────────┐
│         DATA VALIDATION TEMPLATE                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  INPUT PARAMETERS:                                      │
│  ┌──────────────────────────────────────────────┐      │
│  │ • data-path: "s3://bucket/data.csv"          │      │
│  │ • validation-rules: JSON                     │      │
│  │   {                                          │      │
│  │     "check_schema": true,                    │      │
│  │     "check_nulls": true,                     │      │
│  │     "check_duplicates": true,                │      │
│  │     "min_records": 1000                      │      │
│  │   }                                          │      │
│  │ • fail-on-error: false                       │      │
│  │ • data-format: "csv"                         │      │
│  └──────────────────────────────────────────────┘      │
│                      │                                  │
│                      ▼                                  │
│  ┌──────────────────────────────────────────────┐      │
│  │           VALIDATION PROCESS                 │      │
│  │                                              │      │
│  │  1. Load data from path                      │      │
│  │     ├─ Read file metadata                    │      │
│  │     └─ Check file accessibility              │      │
│  │                                              │      │
│  │  2. Schema validation                        │      │
│  │     ├─ Check column names                    │      │
│  │     ├─ Verify data types                     │      │
│  │     └─ Validate constraints                  │      │
│  │                                              │      │
│  │  3. Data quality checks                      │      │
│  │     ├─ NULL value detection                  │      │
│  │     ├─ Duplicate detection                   │      │
│  │     ├─ Record count validation               │      │
│  │     └─ Value range checks                    │      │
│  │                                              │      │
│  │  4. Generate report                          │      │
│  │     ├─ Collect errors                        │      │
│  │     ├─ Collect warnings                      │      │
│  │     └─ Calculate metrics                     │      │
│  └──────────────────────────────────────────────┘      │
│                      │                                  │
│                      ▼                                  │
│  OUTPUT PARAMETERS:                                     │
│  ┌──────────────────────────────────────────────┐      │
│  │ • validation-status: "success" | "failed"    │      │
│  │ • error-count: 0                             │      │
│  │ • validation-report: {                       │      │
│  │     "timestamp": "2024-04-23T10:00:00Z",     │      │
│  │     "status": "success",                     │      │
│  │     "errors": [],                            │      │
│  │     "warnings": ["Found 5 NULL values"],     │      │
│  │     "metrics": {                             │      │
│  │       "total_records": 10000,                │      │
│  │       "null_count": 5,                       │      │
│  │       "duplicate_count": 3                   │      │
│  │     }                                        │      │
│  │   }                                          │      │
│  └──────────────────────────────────────────────┘      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

### 4. ETL Processing Template - Типы трансформаций

```
┌────────────────────────────────────────────────────────────────┐
│              ETL PROCESSING TEMPLATE                           │
└────────────────────────────────────────────────────────────────┘

INPUT DATA
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        EXTRACT PHASE                            │
│  • Read from source (S3, HDFS, Local)                          │
│  • Parse format (CSV, JSON, Parquet, Avro)                     │
│  • Validate structure                                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │  TRANSFORM    │
                    │   DISPATCHER  │
                    └───┬───────────┘
                        │
        ┌───────────────┼───────────────┬────────────────┐
        │               │               │                │
        ▼               ▼               ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   FILTER     │ │  AGGREGATE   │ │     JOIN     │ │   ENRICH     │
├──────────────┤ ├──────────────┤ ├──────────────┤ ├──────────────┤
│              │ │              │ │              │ │              │
│ • Apply      │ │ • Group by   │ │ • Load right │ │ • Lookup     │
│   conditions │ │   columns    │ │   table      │ │   reference  │
│              │ │              │ │              │ │   data       │
│ • Keep/      │ │ • Calculate  │ │ • Match keys │ │              │
│   Remove     │ │   aggregates │ │              │ │ • Add new    │
│   rows       │ │   (sum, avg, │ │ • Combine    │ │   columns    │
│              │ │   count)     │ │   records    │ │              │
│              │ │              │ │              │ │ • Enhance    │
│ Output:      │ │ Output:      │ │ Output:      │ │   data       │
│ Filtered     │ │ Aggregated   │ │ Joined       │ │              │
│ dataset      │ │ summary      │ │ dataset      │ │ Output:      │
│              │ │              │ │              │ │ Enriched     │
│              │ │              │ │              │ │ dataset      │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │                │
       └────────────────┴────────────────┴────────────────┘
                              │
                              ▼
            ┌────────────────────────────────────┐
            │         LOAD PHASE                 │
            │                                    │
            │ • Convert to target format         │
            │ • Partition data (if needed)       │
            │ • Write to destination             │
            │ • Generate metadata                │
            └──────────────┬─────────────────────┘
                           │
                           ▼
                    OUTPUT DATA
                    + METADATA
```

---

### 5. Conditional Execution Template - Типы условий

```
┌───────────────────────────────────────────────────────────────┐
│            CONDITIONAL EXECUTION TEMPLATE                     │
└───────────────────────────────────────────────────────────────┘

INPUT: condition-type, condition-value, operator, threshold
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│                    CONDITION EVALUATOR                        │
└───────────────────────────────────────────────────────────────┘
    │
    ├─────────────┬─────────────┬─────────────┬─────────────┐
    │             │             │             │             │
    ▼             ▼             ▼             ▼             ▼
┌────────┐  ┌─────────┐  ┌────────┐  ┌────────┐  ┌────────┐
│THRESHOLD│ │ STATUS  │  │ REGEX  │  │ RANGE  │  │CUSTOM  │
└────────┘  └─────────┘  └────────┘  └────────┘  └────────┘

THRESHOLD:                     STATUS:
  value: 1500                    value: "success"
  threshold: 1000                threshold: "success"
  operator: gt (>)               operator: eq (==)
  ▼                             ▼
  1500 > 1000                   "success" == "success"
  = TRUE                        = TRUE
  ▼                             ▼
  EXECUTE                       EXECUTE

REGEX:                         RANGE:
  value: "user-2024-001"         value: 150
  pattern: /user-\d{4}-\d+/      range: "100,200"
  operator: matches              operator: in
  ▼                             ▼
  Pattern matches               100 <= 150 <= 200
  = TRUE                        = TRUE
  ▼                             ▼
  EXECUTE                       EXECUTE

                    │
                    ▼
    ┌──────────────────────────────┐
    │   DECISION MAKER             │
    │                              │
    │   condition_result: true     │
    │            ↓                 │
    │   execution_decision:        │
    │   "execute" | "skip"         │
    │            ↓                 │
    │   decision_reason:           │
    │   "1500 > 1000"              │
    └──────────────┬───────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
    ┌────────┐           ┌────────┐
    │EXECUTE │           │  SKIP  │
    │ NEXT   │           │  NEXT  │
    │ STEP   │           │  STEP  │
    └────────┘           └────────┘
```

---

### 6. Batch File Processor Template - Параллельная обработка

```
┌─────────────────────────────────────────────────────────────┐
│          BATCH FILE PROCESSOR TEMPLATE                      │
└─────────────────────────────────────────────────────────────┘

INPUT: source-directory, file-pattern, operation, parallel-workers
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│              FILE DISCOVERY PHASE                           │
│                                                             │
│  source-directory: "s3://data-lake/raw/"                    │
│  file-pattern: "*.csv"                                      │
│         ↓                                                   │
│  ┌──────────────────────────────────────────┐              │
│  │  Discovered Files:                       │              │
│  │  • data1.csv      (1 MB)                 │              │
│  │  • data2.csv      (2 MB)                 │              │
│  │  • data3.csv      (512 KB)               │              │
│  │  • data4.csv      (4 MB)                 │              │
│  │  • data5.csv      (1.5 MB)               │              │
│  │  • data6.csv      (3 MB)                 │              │
│  │  • ...                                   │              │
│  └──────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           PARALLEL PROCESSING (Workers: 4)                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Worker 1          Worker 2          Worker 3   Worker 4  │
│   ┌──────┐         ┌──────┐         ┌──────┐   ┌──────┐  │
│   │File 1│         │File 2│         │File 3│   │File 4│  │
│   └───┬──┘         └───┬──┘         └───┬──┘   └───┬──┘  │
│       │                │                │            │     │
│       ▼                ▼                ▼            ▼     │
│   ┌────────┐      ┌────────┐      ┌────────┐  ┌────────┐ │
│   │Process │      │Process │      │Process │  │Process │ │
│   └───┬────┘      └───┬────┘      └───┬────┘  └───┬────┘ │
│       │                │                │            │     │
│       ▼                ▼                ▼            ▼     │
│   ✓ Success        ✓ Success        ✓ Success   ✗ Failed │
│                                                             │
│   Continue with next batch...                              │
│   Worker 1          Worker 2          Worker 3   Worker 4  │
│   ┌──────┐         ┌──────┐         ┌──────┐   ┌──────┐  │
│   │File 5│         │File 6│         │File 7│   │File 4│  │
│   │      │         │      │         │      │   │(retry)│  │
│   └──────┘         └──────┘         └──────┘   └──────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    OPERATION TYPES                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ANALYZE          COPY             COMPRESS       TRANSFORM │
│  ┌────────┐      ┌────────┐      ┌────────┐     ┌────────┐│
│  │• Size  │      │Source  │      │Original│     │Format  ││
│  │• Format│  →   │  ↓     │  →   │  ↓     │ →   │Change ││
│  │• Schema│      │Target  │      │Comp.   │     │Schema ││
│  │• Stats │      │        │      │70% ↓   │     │Modify ││
│  └────────┘      └────────┘      └────────┘     └────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      RESULTS                                │
│                                                             │
│  files_processed: 15                                        │
│  files_failed: 1                                            │
│  total_size: 25,600,000 bytes (24.4 MB)                    │
│  processing_time: 45.3 seconds                              │
│                                                             │
│  file_list: [                                               │
│    {                                                        │
│      "file": "data1.csv",                                   │
│      "status": "success",                                   │
│      "size": 1048576,                                       │
│      "operation": "compress",                               │
│      "compressed_size": 314572,                             │
│      "compression_ratio": "70.0%"                           │
│    },                                                       │
│    ...                                                      │
│  ]                                                          │
└─────────────────────────────────────────────────────────────┘
```

---

### 7. Notification Template - Мультиканальная отправка

```
┌───────────────────────────────────────────────────────────────┐
│              NOTIFICATION TEMPLATE                            │
└───────────────────────────────────────────────────────────────┘

INPUT:
  • notification-type: "slack"
  • recipients: "#data-alerts"
  • subject: "Pipeline Completed"
  • message: "Processing finished successfully"
  • status: "success"
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│                 NOTIFICATION FORMATTER                        │
│                                                               │
│  Status → Emoji Mapping:                                     │
│  • success → ✅                                               │
│  • warning → ⚠️                                               │
│  • error   → ❌                                               │
│  • info    → ℹ️                                               │
│                                                               │
│  Formatted Message:                                          │
│  ┌──────────────────────────────────────────┐               │
│  │ ✅ Pipeline Completed                     │               │
│  │                                          │               │
│  │ Processing finished successfully         │               │
│  │                                          │               │
│  │ Timestamp: 2024-04-23T10:30:00Z         │               │
│  │ Status: success                          │               │
│  └──────────────────────────────────────────┘               │
└───────────────────────────┬───────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│    SLACK     │    │    EMAIL     │    │    TEAMS     │
├──────────────┤    ├──────────────┤    ├──────────────┤
│              │    │              │    │              │
│ POST to      │    │ SMTP Send    │    │ POST to      │
│ webhook      │    │              │    │ connector    │
│              │    │ To: team@... │    │              │
│ Payload:     │    │ Subject: ... │    │ Payload:     │
│ {            │    │ Body: ...    │    │ {            │
│   "text":    │    │              │    │   "@type":   │
│   "...",     │    │ HTML:        │    │   "Message   │
│   "emoji":   │    │ <h1>...</h1> │    │   Card",     │
│   "✅"       │    │ <p>...</p>   │    │   "title":   │
│ }            │    │              │    │   "..."      │
│              │    │              │    │ }            │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       ▼                   ▼                   ▼
   ┌────────┐         ┌────────┐         ┌────────┐
   │Delivered│        │Delivered│        │Delivered│
   └────────┘         └────────┘         └────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │ OUTPUT PARAMETERS │
                  │                   │
                  │ notification_sent:│
                  │   "true"          │
                  │                   │
                  │ send_timestamp:   │
                  │   "2024-04-23..."│
                  └───────────────────┘
```

---

### 8. Полный поток данных в Main Workflow

```
                        ┌──────────────┐
                        │   S3 Bucket  │
                        │  Raw Data    │
                        └──────┬───────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  1. Validation      │
                    │  Template           │
                    │                     │
                    │  ✓ Schema OK        │
                    │  ✓ No critical err. │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  2. Conditional     │
                    │  Check              │
                    │                     │
                    │  status == success? │
                    └──────┬───────┬──────┘
                           │ YES   │ NO
                           │       │
                           │       └─────────────┐
                           ▼                     │
                    ┌─────────────────────┐     │
                    │  3. ETL Processing  │     │
                    │  Template           │     │
                    │                     │     │
                    │  Filter → Transform │     │
                    │  CSV → Parquet      │     │
                    │                     │     │
                    │  10,000 records     │     │
                    │  → 8,000 filtered   │     │
                    └──────────┬──────────┘     │
                               │                │
                               ▼                │
                    ┌─────────────────────┐     │
                    │  4. Quality Check   │     │
                    │  (Conditional)      │     │
                    │                     │     │
                    │  records >= 1000?   │     │
                    └──────┬───────┬──────┘     │
                           │ YES   │ NO         │
                           │       └────┐       │
                           ▼            │       │
                    ┌─────────────────┐ │       │
                    │  5. Batch       │ │       │
                    │  Processing     │ │       │
                    │                 │ │       │
                    │  Compress 15    │ │       │
                    │  files          │ │       │
                    │  24MB → 7.2MB   │ │       │
                    └──────┬──────────┘ │       │
                           │            │       │
                           ▼            ▼       ▼
                    ┌──────────────────────────────┐
                    │  6. Notification             │
                    │  Template                    │
                    │                              │
                    │  → Slack: Success ✅         │
                    │  → Email: Report sent        │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                            ┌─────────────┐
                            │ S3 Bucket   │
                            │ Processed   │
                            └─────────────┘
```

---

### 9. Обработка ошибок и retry логика

```
                        ┌──────────────┐
                        │  Workflow    │
                        │  Step        │
                        └──────┬───────┘
                               │
                               ▼
                        ┌─────────────┐
                        │  Execute    │
                        └──────┬──────┘
                               │
                    ┌──────────┴──────────┐
                    │ Success?            │
                    └──┬───────────────┬──┘
                  YES  │               │ NO
                       ▼               ▼
                  ┌─────────┐    ┌──────────────┐
                  │Continue │    │ Retry Logic  │
                  │to Next  │    └──────┬───────┘
                  └─────────┘           │
                                        ▼
                               ┌─────────────────┐
                               │ Retry Count < 2?│
                               └────┬────────┬───┘
                                 YES│        │NO
                                    ▼        ▼
                             ┌──────────┐  ┌──────────┐
                             │Backoff   │  │Fail      │
                             │Wait 30s  │  │Workflow  │
                             │* 2^retry │  └────┬─────┘
                             └────┬─────┘       │
                                  │             ▼
                                  │    ┌─────────────────┐
                                  │    │ onExit Handler  │
                                  │    │                 │
                                  │    │ • Cleanup       │
                                  │    │ • Notification  │
                                  │    │ • Log errors    │
                                  │    └─────────────────┘
                                  │
                                  └──────▶ Retry Execute
```

---

## 🔍 Интеграции и расширения

### Интеграция с внешними системами

```
┌────────────────────────────────────────────────────────────┐
│              EXTERNAL INTEGRATIONS                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Data Sources:          Processing:        Destinations:   │
│  ┌──────────┐          ┌──────────┐       ┌──────────┐   │
│  │   S3     │────┐     │  Spark   │  ┌───▶│  S3      │   │
│  └──────────┘    │     └──────────┘  │    └──────────┘   │
│                  │                    │                    │
│  ┌──────────┐    │     ┌──────────┐  │    ┌──────────┐   │
│  │  HDFS    │────┼────▶│  Pandas  │──┼───▶│Snowflake │   │
│  └──────────┘    │     └──────────┘  │    └──────────┘   │
│                  │                    │                    │
│  ┌──────────┐    │     ┌──────────┐  │    ┌──────────┐   │
│  │PostgreSQL│────┘     │  Dask    │  └───▶│BigQuery  │   │
│  └──────────┘          └──────────┘       └──────────┘   │
│                                                            │
│  Monitoring:            Notifications:                     │
│  ┌──────────┐          ┌──────────┐                       │
│  │Prometheus│          │  Slack   │                       │
│  └────┬─────┘          └──────────┘                       │
│       │                                                    │
│  ┌────▼─────┐          ┌──────────┐                       │
│  │ Grafana  │          │  Email   │                       │
│  └──────────┘          └──────────┘                       │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

Эти диаграммы помогают понять:
1. Общую архитектуру системы шаблонов
2. Поток данных в основном пайплайне
3. Внутреннюю работу каждого шаблона
4. Логику принятия решений
5. Параллельную обработку
6. Обработку ошибок и retry механизмы
7. Интеграции с внешними системами

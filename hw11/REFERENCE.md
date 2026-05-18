# 📋 Справочник параметров WorkflowTemplate

Быстрый справочник всех входных и выходных параметров для каждого шаблона.

---

## 📊 Сводная таблица шаблонов

| # | Шаблон | Основная задача | Входов | Выходов | Артефактов |
|---|--------|----------------|--------|---------|------------|
| 1 | Data Validation | Проверка данных | 4 | 3 | 0 |
| 2 | ETL Processing | Обработка данных | 7 | 3 | 1 |
| 3 | Notification | Отправка уведомлений | 7 | 2 | 0 |
| 4 | Conditional Execution | Условная логика | 5 | 3 | 0 |
| 5 | Batch File Processor | Пакетная обработка | 6 | 4 | 0 |
| **ВСЕГО** | | | **29** | **15** | **1** |

---

## 1️⃣ Data Validation Template

**templateRef:** `data-validation-template` / `validate`

### Входные параметры

| Параметр | Тип | Обязательный | По умолчанию | Описание |
|----------|-----|--------------|--------------|----------|
| `data-path` | string | ✅ Да | - | Путь к файлу данных (S3, local, URL) |
| `validation-rules` | JSON | ❌ Нет | `{"check_schema": true, ...}` | Правила валидации в JSON формате |
| `fail-on-error` | boolean | ❌ Нет | `false` | Завершать ли workflow при ошибке |
| `data-format` | string | ❌ Нет | `csv` | Формат: csv, json, parquet, avro |

### Validation Rules - структура JSON

```json
{
  "check_schema": true,              // boolean - проверка схемы
  "check_nulls": true,                // boolean - проверка NULL
  "check_duplicates": true,           // boolean - проверка дубликатов
  "min_records": 100,                 // integer - минимум записей
  "max_records": 1000000,             // integer - максимум записей
  "required_columns": ["col1", "col2"], // array - обязательные колонки
  "column_types": {                   // object - типы колонок
    "age": "integer",
    "email": "string"
  }
}
```

### Выходные параметры

| Параметр | Тип | Формат | Описание |
|----------|-----|--------|----------|
| `validation-status` | string | `success` \| `failed` | Результат валидации |
| `error-count` | integer | `0-N` | Количество найденных ошибок |
| `validation-report` | JSON | См. ниже | Детальный отчет о валидации |

### Validation Report - структура JSON

```json
{
  "timestamp": "2024-04-23T10:00:00Z",
  "data_path": "s3://bucket/data.csv",
  "data_format": "csv",
  "status": "success",
  "error_count": 0,
  "warning_count": 2,
  "errors": [],
  "warnings": [
    "Found 5 NULL values in column 'email'",
    "Found 3 duplicate records"
  ],
  "rules_applied": {
    "check_schema": true,
    "check_nulls": true,
    "check_duplicates": true
  }
}
```

### Пример использования

```yaml
- name: validate-data
  templateRef:
    name: data-validation-template
    template: validate
  arguments:
    parameters:
    - name: data-path
      value: "s3://my-bucket/data.csv"
    - name: validation-rules
      value: '{"check_schema": true, "check_nulls": true, "min_records": 1000}'
    - name: fail-on-error
      value: "true"
    - name: data-format
      value: "csv"
```

---

## 2️⃣ ETL Processing Template

**templateRef:** `etl-processing-template` / `process`

### Входные параметры

| Параметр | Тип | Обязательный | По умолчанию | Описание |
|----------|-----|--------------|--------------|----------|
| `source-path` | string | ✅ Да | - | Путь к исходным данным |
| `target-path` | string | ✅ Да | - | Путь для сохранения результата |
| `transformation-type` | string | ❌ Нет | `filter` | Тип: filter, aggregate, join, enrich |
| `transformation-config` | JSON | ❌ Нет | `{}` | Конфигурация трансформации |
| `chunk-size` | integer | ❌ Нет | `1000` | Размер чанка для обработки |
| `source-format` | string | ❌ Нет | `csv` | Формат входных данных |
| `target-format` | string | ❌ Нет | `parquet` | Формат выходных данных |

### Transformation Types

#### Filter
```json
{
  "filter_column": "status",
  "filter_value": "completed",
  "filter_operator": "eq"
}
```

#### Aggregate
```json
{
  "group_by": ["customer_id", "date"],
  "aggregations": {
    "amount": "sum",
    "order_id": "count"
  }
}
```

#### Join
```json
{
  "join_type": "left",
  "join_table": "s3://bucket/reference.parquet",
  "join_on": "customer_id"
}
```

#### Enrich
```json
{
  "lookup_table": "s3://bucket/enrichment.csv",
  "lookup_key": "id",
  "enrich_columns": ["category", "region"]
}
```

### Выходные параметры

| Параметр | Тип | Формат | Описание |
|----------|-----|--------|----------|
| `records-processed` | integer | `0-N` | Количество обработанных записей |
| `processing-time` | float | `0.00` (секунды) | Время обработки |
| `output-size` | integer | `0-N` (байты) | Размер выходного файла |

### Артефакты

| Артефакт | Путь | Описание |
|----------|------|----------|
| `processed-data` | `/tmp/output` | Обработанные данные |

### Пример использования

```yaml
- name: etl-process
  templateRef:
    name: etl-processing-template
    template: process
  arguments:
    parameters:
    - name: source-path
      value: "s3://bucket/input.csv"
    - name: target-path
      value: "s3://bucket/output/"
    - name: transformation-type
      value: "filter"
    - name: transformation-config
      value: '{"filter_column": "status", "filter_value": "completed"}'
    - name: chunk-size
      value: "5000"
    - name: source-format
      value: "csv"
    - name: target-format
      value: "parquet"
```

---

## 3️⃣ Notification Template

**templateRef:** `notification-template` / `send`

### Входные параметры

| Параметр | Тип | Обязательный | По умолчанию | Описание |
|----------|-----|--------------|--------------|----------|
| `notification-type` | string | ❌ Нет | `slack` | Тип: email, slack, webhook, teams |
| `recipients` | string | ✅ Да | - | Получатели (через запятую) |
| `subject` | string | ✅ Да | - | Тема сообщения |
| `message` | string | ✅ Да | - | Текст сообщения |
| `status` | string | ❌ Нет | `info` | Статус: success, warning, error, info |
| `webhook-url` | string | ❌ Нет | `""` | URL webhook (для slack/teams) |
| `include-metadata` | boolean | ❌ Нет | `true` | Включать метаданные workflow |

### Notification Types

| Тип | Описание | Требуемые параметры |
|-----|----------|---------------------|
| `slack` | Slack webhook | recipients, webhook-url |
| `email` | Email через SMTP | recipients |
| `teams` | Microsoft Teams | recipients, webhook-url |
| `webhook` | Generic HTTP POST | webhook-url |

### Status → Emoji Mapping

| Status | Emoji | Цвет |
|--------|-------|------|
| `success` | ✅ | Зеленый |
| `warning` | ⚠️ | Желтый |
| `error` | ❌ | Красный |
| `info` | ℹ️ | Синий |

### Выходные параметры

| Параметр | Тип | Формат | Описание |
|----------|-----|--------|----------|
| `notification-sent` | boolean | `true` \| `false` | Успешность отправки |
| `send-timestamp` | string | ISO 8601 | Время отправки |

### Пример использования

```yaml
- name: send-notification
  templateRef:
    name: notification-template
    template: send
  arguments:
    parameters:
    - name: notification-type
      value: "slack"
    - name: recipients
      value: "#data-alerts"
    - name: subject
      value: "Pipeline Completed"
    - name: message
      value: "Data processing finished successfully"
    - name: status
      value: "success"
    - name: webhook-url
      value: "https://hooks.slack.com/services/YOUR/WEBHOOK"
    - name: include-metadata
      value: "true"
```

---

## 4️⃣ Conditional Execution Template

**templateRef:** `conditional-execution-template` / `evaluate`

### Входные параметры

| Параметр | Тип | Обязательный | По умолчанию | Описание |
|----------|-----|--------------|--------------|----------|
| `condition-type` | string | ❌ Нет | `threshold` | Тип: threshold, status, regex, range |
| `condition-value` | string | ✅ Да | - | Значение для проверки |
| `condition-operator` | string | ❌ Нет | `gt` | Оператор сравнения |
| `threshold` | string | ❌ Нет | `0` | Пороговое значение |
| `default-decision` | string | ❌ Нет | `skip` | Решение по умолчанию: execute, skip |

### Condition Types

| Тип | Описание | Применяемые операторы |
|-----|----------|----------------------|
| `threshold` | Числовое сравнение | gt, lt, gte, lte, eq, ne |
| `status` | Проверка статуса | eq, ne, contains |
| `regex` | Регулярное выражение | matches |
| `range` | Проверка диапазона | in |

### Operators (Операторы)

| Оператор | Название | Описание | Пример |
|----------|----------|----------|--------|
| `gt` | Greater Than | Больше | `100 > 50` |
| `lt` | Less Than | Меньше | `50 < 100` |
| `gte` | Greater or Equal | Больше или равно | `100 >= 100` |
| `lte` | Less or Equal | Меньше или равно | `50 <= 100` |
| `eq` | Equal | Равно | `"success" == "success"` |
| `ne` | Not Equal | Не равно | `"failed" != "success"` |
| `contains` | Contains | Содержит | `"completed" in "status:completed"` |
| `matches` | Regex Match | Regex совпадение | `"test123" matches /test\d+/` |
| `in` | In Range | В диапазоне | `100 <= 150 <= 200` |

### Выходные параметры

| Параметр | Тип | Формат | Описание |
|----------|-----|--------|----------|
| `condition-result` | boolean | `true` \| `false` | Результат проверки условия |
| `execution-decision` | string | `execute` \| `skip` | Решение о выполнении |
| `decision-reason` | string | Текст | Причина принятого решения |

### Примеры использования

#### Threshold Check
```yaml
- name: check-threshold
  templateRef:
    name: conditional-execution-template
    template: evaluate
  arguments:
    parameters:
    - name: condition-type
      value: "threshold"
    - name: condition-value
      value: "{{steps.etl.outputs.parameters.records-processed}}"
    - name: condition-operator
      value: "gte"
    - name: threshold
      value: "1000"
```

#### Status Check
```yaml
- name: check-status
  templateRef:
    name: conditional-execution-template
    template: evaluate
  arguments:
    parameters:
    - name: condition-type
      value: "status"
    - name: condition-value
      value: "{{steps.validate.outputs.parameters.validation-status}}"
    - name: condition-operator
      value: "eq"
    - name: threshold
      value: "success"
```

#### Range Check
```yaml
- name: check-range
  templateRef:
    name: conditional-execution-template
    template: evaluate
  arguments:
    parameters:
    - name: condition-type
      value: "range"
    - name: condition-value
      value: "150"
    - name: threshold
      value: "100,200"
```

---

## 5️⃣ Batch File Processor Template

**templateRef:** `batch-file-processor-template` / `process-batch`

### Входные параметры

| Параметр | Тип | Обязательный | По умолчанию | Описание |
|----------|-----|--------------|--------------|----------|
| `source-directory` | string | ✅ Да | - | Директория с файлами |
| `file-pattern` | string | ❌ Нет | `*.*` | Паттерн фильтрации (glob) |
| `operation` | string | ❌ Нет | `analyze` | Операция над файлами |
| `target-directory` | string | ❌ Нет | `/tmp/target` | Целевая директория |
| `parallel-workers` | integer | ❌ Нет | `4` | Количество воркеров |
| `fail-fast` | boolean | ❌ Нет | `false` | Остановка при первой ошибке |

### Operations

| Операция | Описание | Требует target-directory |
|----------|----------|-------------------------|
| `analyze` | Анализ файлов (размер, формат) | ❌ Нет |
| `copy` | Копирование файлов | ✅ Да |
| `move` | Перемещение файлов | ✅ Да |
| `transform` | Трансформация файлов | ✅ Да |
| `compress` | Сжатие файлов | ❌ Нет |

### File Patterns (примеры)

| Паттерн | Описание |
|---------|----------|
| `*.*` | Все файлы |
| `*.csv` | Только CSV файлы |
| `*.json` | Только JSON файлы |
| `data*.parquet` | Parquet файлы начинающиеся с "data" |
| `2024-*.csv` | CSV файлы начинающиеся с "2024-" |

### Выходные параметры

| Параметр | Тип | Формат | Описание |
|----------|-----|--------|----------|
| `files-processed` | integer | `0-N` | Количество обработанных файлов |
| `files-failed` | integer | `0-N` | Количество файлов с ошибками |
| `total-size` | integer | `0-N` (байты) | Общий размер файлов |
| `file-list` | JSON | Array | Список обработанных файлов |

### File List - структура JSON

```json
[
  {
    "file": "data1.csv",
    "size": 1048576,
    "status": "success",
    "operation": "compress",
    "original_size": 1048576,
    "compressed_size": 314572,
    "compression_ratio": "70.0%",
    "timestamp": "2024-04-23T10:00:00Z"
  },
  {
    "file": "data2.csv",
    "size": 2048000,
    "status": "success",
    "operation": "analyze"
  }
]
```

### Пример использования

```yaml
- name: batch-process
  templateRef:
    name: batch-file-processor-template
    template: process-batch
  arguments:
    parameters:
    - name: source-directory
      value: "s3://data-lake/raw/"
    - name: file-pattern
      value: "*.csv"
    - name: operation
      value: "compress"
    - name: target-directory
      value: "s3://data-lake/compressed/"
    - name: parallel-workers
      value: "10"
    - name: fail-fast
      value: "false"
```

---

## 📊 Матрица совместимости

### Data Formats

| Формат | Validation | ETL Input | ETL Output | Batch Processing |
|--------|-----------|-----------|------------|------------------|
| CSV | ✅ | ✅ | ✅ | ✅ |
| JSON | ✅ | ✅ | ✅ | ✅ |
| Parquet | ✅ | ✅ | ✅ | ✅ |
| Avro | ✅ | ✅ | ✅ | ❌ |

### Storage Locations

| Location | Все шаблоны |
|----------|------------|
| S3 | ✅ Поддерживается |
| HDFS | ✅ Поддерживается |
| Local | ✅ Поддерживается |
| HTTP/HTTPS | ✅ Поддерживается (read-only) |

---

## 🔗 Связывание шаблонов

### Передача outputs между шагами

```yaml
# Шаг 1: Validation
- name: validate
  templateRef:
    name: data-validation-template
    template: validate
  arguments:
    parameters:
    - name: data-path
      value: "s3://bucket/data.csv"

# Шаг 2: Conditional (использует output из шага 1)
- name: check
  templateRef:
    name: conditional-execution-template
    template: evaluate
  arguments:
    parameters:
    - name: condition-value
      value: "{{steps.validate.outputs.parameters.validation-status}}"

# Шаг 3: ETL (выполняется условно)
- name: process
  templateRef:
    name: etl-processing-template
    template: process
  when: "{{steps.check.outputs.parameters.execution-decision}} == execute"
```

### Типичные цепочки

#### Validation → Conditional → ETL
```
Validate → Check Status → Process (if valid)
```

#### ETL → Conditional → Batch
```
ETL → Check Records Count → Batch Process (if enough records)
```

#### Any Step → Notification
```
Any Step → Notify (always or on condition)
```

---

## 📝 Шпаргалка по использованию

### Быстрые команды

```bash
# Применить шаблоны
kubectl apply -f workflow-templates.yaml -n argo

# Запустить workflow
kubectl create -f main-workflow.yaml -n argo

# Список workflows
argo list -n argo

# Логи
argo logs <workflow-name> -n argo

# Статус
argo get <workflow-name> -n argo
```

### Часто используемые параметры

```yaml
# Validation
- name: data-path
  value: "s3://bucket/data.csv"
- name: validation-rules
  value: '{"check_schema": true, "check_nulls": true}'

# ETL
- name: transformation-type
  value: "filter"  # или aggregate, join, enrich

# Notification
- name: status
  value: "success"  # или warning, error, info

# Conditional
- name: condition-operator
  value: "gte"  # или gt, lt, eq, ne, contains

# Batch
- name: operation
  value: "compress"  # или analyze, copy, move, transform
```

---

**Это полный справочник всех параметров. Для примеров использования см. [examples.yaml](examples.yaml)**

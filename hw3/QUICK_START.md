# Быстрый старт

## 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

## 2. Быстрое тестирование (рекомендуется для начала)

```bash
python run_tests.py quick
```

Это запустит тест на 1 миллионе записей (~100MB). Займет несколько минут.

## 3. Просмотр результатов

Результаты автоматически сохраняются после выполнения тестов в корневой директории:
- `performance_results.csv` - таблица с метриками
- `performance_report_quick.md` - детальный отчет для quick теста
- `performance_report_medium.md` - детальный отчет для medium теста
- `performance_report_full.md` - детальный отчет для full теста

## 4. Полное тестирование (~10GB)

```bash
python main.py
```

ИЛИ

```bash
python run_tests.py full
```

## 5. Средний тест (5 млн записей)

```bash
python run_tests.py medium
```

## Дополнительные возможности

### Генерация данных без тестирования

```bash
python generate_data.py 1000000
```

### Генерация только определенных форматов

```bash
python generate_data.py 500000 parquet csv
```

## Где найти результаты

Результаты сохраняются автоматически в корневой директории после каждого теста:
- `performance_results.csv` - таблица с метриками (перезаписывается при каждом тесте)
- `performance_report_quick.md` - детальный отчет для quick теста
- `performance_report_medium.md` - детальный отчет для medium теста
- `performance_report_full.md` - детальный отчет для full теста

Файлы данных сохраняются в папке test_data/:
- `test_data/parquet/` - Parquet файлы
- `test_data/avro/` - Avro файлы
- `test_data/csv/` - CSV файлы
- `test_data/json/` - JSON файлы

## Настройка параметров

Отредактируйте `config.py`:

```python
TARGET_SIZE_GB = 10
NUM_RECORDS = ...
RANDOM_SEED = 42
```

## Ожидаемое время выполнения

- **Quick test (1M records)**: 2-5 минут
- **Medium test (5M records)**: 10-20 минут
- **Full test (~10GB)**: 1-3 часа (в зависимости от железа)

## Системные требования

- **RAM**: минимум 8GB (рекомендуется 16GB для полного теста)
- **Disk**: минимум 40GB свободного места (для всех форматов)
- **Python**: 3.8+

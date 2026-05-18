# Домашнее задание 5: Сравнение производительности DataFrame, RDD и SQL в Apache Spark

## Описание

Этот проект реализует комплексное сравнение производительности различных API Apache Spark:
- DataFrame API vs RDD API
- SQL vs DataFrame API

Проект демонстрирует оптимизации Catalyst и Tungsten на практических примерах.

## Структура проекта

```
hw5/
 main.py                  # Главный скрипт запуска
 config.py               # Конфигурация Spark и параметров
 benchmark.py            # Бенчмарки и тест-кейсы
 data_generator.py       # Генераторы тестовых данных
 report_generator.py     # Генератор отчетов
 requirements.txt        # Зависимости Python
 README.md              # Этот файл
```

## Реализованные кейсы

### Часть 1: DataFrame vs RDD (4 кейса)

1. **Множественные агрегации**
   - DataFrame: одновременное выполнение sum, avg, min, max, count
   - RDD: множественные проходы через данные
   - Оптимизация: single-pass aggregation, code generation

2. **Оконные функции**
   - DataFrame: Window.partitionBy() с row_number()
   - RDD: groupByKey() + локальная сортировка
   - Оптимизация: partition-local sorting, специализированный window operator

3. **Вложенные типы**
   - DataFrame: нативная работа с arrays и structs
   - RDD: ручная сериализация/десериализация
   - Оптимизация: binary format, zero-copy operations

4. **Условная логика**
   - DataFrame: when/otherwise для множественных условий
   - RDD: filter + union для каждого условия
   - Оптимизация: code generation для branching logic

### Часть 2: SQL vs DataFrame API (2 кейса) - БОНУС

1. **Комплексная агрегация с HAVING**
   - Сравнение SQL запроса и DataFrame API
   - Анализ планов выполнения через explain()

2. **Коррелированный подзапрос**
   - SQL с коррелированным WHERE
   - DataFrame API с явным join
   - Оптимизация: subquery decorrelation

## Установка и запуск

### Требования

- Python 3.8+
- Apache Spark 3.4+
- Java 8 или 11

**ИЛИ**

- Docker и Docker Compose (рекомендуется)

### Установка зависимостей

#### Вариант 1: Docker (рекомендуется)

Docker автоматически настроит все зависимости:

```bash
# Сборка образа
docker-compose build

# Запуск быстрого теста
docker-compose up spark-benchmark

# Или используйте PowerShell скрипт (Windows)
.\run_docker.ps1 small

# Или Bash скрипт (Linux/MacOS)
./run_docker.sh small
```

Результаты будут сохранены в папку `./reports/`

#### Вариант 2: Локальная установка

```bash
pip install -r requirements.txt
```

### Запуск бенчмарков

#### С Docker

```bash
# Быстрый тест (10,000 строк)
docker-compose up spark-benchmark

# Средний тест (100,000 строк)
docker-compose --profile medium up spark-benchmark-medium

# Большой тест (1,000,000 строк)
docker-compose --profile large up spark-benchmark-large

# Или используйте скрипты:
.\run_docker.ps1 small   # Windows
./run_docker.sh medium   # Linux/MacOS
```

#### Локально

```bash
# Запуск с размером датасета по умолчанию (medium = 100,000 строк)
python main.py

# Запуск с малым датасетом (10,000 строк)
python main.py small

# Запуск с большим датасетом (1,000,000 строк)
python main.py large
```

Доступные размеры датасетов:
- `small`: 10,000 строк
- `medium`: 100,000 строк (по умолчанию)
- `large`: 1,000,000 строк

### Результаты

После выполнения бенчмарков будет создан файл `reports/performance_report_<размер>.md` с:
- Таблицами производительности
- Подробным описанием каждого кейса
- Анализом оптимизаций Catalyst/Tungsten
- Выводами и рекомендациями

Папка `reports/` монтируется как volume в Docker, поэтому результаты доступны на хост-машине.

## Ключевые оптимизации

### Catalyst Optimizer

1. **Predicate Pushdown** - перенос фильтров ближе к источнику данных
2. **Projection Pruning** - чтение только необходимых колонок
3. **Constant Folding** - вычисление константных выражений на этапе планирования
4. **Join Reordering** - оптимальный порядок соединений
5. **Subquery Decorrelation** - преобразование коррелированных подзапросов в joins

### Tungsten Execution Engine

1. **Whole-Stage Code Generation** - генерация Java bytecode для всего stage
2. **Off-Heap Memory Management** - управление памятью вне JVM heap
3. **Cache-Aware Computation** - оптимизация для CPU cache
4. **Binary Processing** - UnsafeRow format без десериализации
5. **Vectorized Parquet Reader** - пакетное чтение колонок

## Выводы

### DataFrame всегда быстрее RDD когда:
- Выполняются типичные операции (join, aggregation, filter)
- Работаете со структурированными данными
- Нужны оптимизации компилятора и runtime
- Важна производительность

### RDD нужны только когда:
- Очень специфичная низкоуровневая логика
- Работа с произвольными бинарными данными
- Точный контроль над партиционированием
- Legacy код

### SQL vs DataFrame API:
- В 95% случаев дают одинаковую производительность
- SQL может быть быстрее для сложных подзапросов
- DataFrame API лучше для type safety и композиции
- Выбор зависит от предпочтений команды

## Примеры использования

### Запуск только одного теста

Можно модифицировать `config.py`, указав только нужные тесты в `TEST_CASES`.

### Настройка Spark

Измените параметры в `config.py`:

```python
SPARK_CONFIG = {
    "spark.driver.memory": "8g",  # Увеличить память
    "spark.sql.shuffle.partitions": "16",  # Больше партиций
}
```

### Анализ планов выполнения

Бенчмарки автоматически выводят планы выполнения для SQL vs DataFrame кейсов.
Для дополнительного анализа можно использовать:

```python
df.explain(extended=True)  # Полный план
df.explain("cost")         # С информацией о стоимости
```

## Дополнительные материалы

- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Catalyst Optimizer Deep Dive](https://databricks.com/blog/2015/04/13/deep-dive-into-spark-sqls-catalyst-optimizer.html)
- [Project Tungsten](https://databricks.com/blog/2015/04/28/project-tungsten-bringing-spark-closer-to-bare-metal.html)

## Автор

Домашнее задание для курса Data Pipelines, HSE

## Лицензия

MIT

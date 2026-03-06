# Домашнее задание 5: Анализ производительности Spark

## Задание

Реализовать сравнительный анализ производительности различных API Apache Spark:

### Часть 1: DataFrame vs RDD (обязательно)
Реализовать 3 кейса, где DataFrame гарантированно быстрее RDD. Для каждого кейса:
- ✅ Привести код для DataFrame и RDD подходов
- ✅ Измерить производительность
- ✅ Объяснить, какая оптимизация Catalyst/Tungsten дает выигрыш

### Часть 2: SQL vs DataFrame API (бонус *)
Найти 2 кейса, где SQL запрос выполняется быстрее или с другой эффективностью, чем DataFrame API:
- ✅ Сравнить планы выполнения через explain()
- ✅ Объяснить причину разницы

### Результат
- ✅ Отчет с таблицами производительности
- ✅ Выводы о том, когда какой API выбирать

## Реализация

### Структура проекта
```
hw5/
├── main.py                  # Точка входа
├── config.py               # Конфигурация
├── benchmark.py            # Бенчмарки (6 кейсов)
├── data_generator.py       # Генерация тестовых данных
├── report_generator.py     # Генерация отчета
├── requirements.txt        # Зависимости
├── README.md              # Документация
├── QUICK_START.md         # Инструкция запуска
└── SUMMARY.md             # Этот файл
```

### Реализованные кейсы

#### 1. Множественные агрегации (DataFrame vs RDD)
**Задача:** Выполнить несколько агрегатных функций (sum, avg, min, max, count) на сгруппированных данных.

**DataFrame подход:**
```python
df.groupBy("category").agg(
    spark_sum("value"), avg("value"), 
    spark_min("value"), spark_max("value"), count("*")
)
```

**RDD подход:**
```python
# Требует отдельного прохода для каждой агрегации
rdd.reduceByKey(lambda a, b: a + b)  # sum
rdd.aggregateByKey(...)               # avg
rdd.reduceByKey(min)                  # min
rdd.reduceByKey(max)                  # max
```

**Оптимизации Catalyst/Tungsten:**
- Single-pass aggregation - все агрегации за один проход
- Whole-stage code generation - генерация оптимального кода
- Off-heap memory buffers - эффективные буферы агрегации

**Ожидаемый выигрыш:** 3-5x

---

#### 2. Оконные функции (DataFrame vs RDD)
**Задача:** Найти топ-N записей в каждой группе.

**DataFrame подход:**
```python
window = Window.partitionBy("category").orderBy(col("value").desc())
df.withColumn("rank", row_number().over(window)).filter(col("rank") <= 3)
```

**RDD подход:**
```python
rdd.groupByKey().flatMapValues(
    lambda records: sorted(records, key=lambda r: r.value, reverse=True)[:3]
)
```

**Оптимизации Catalyst/Tungsten:**
- Partition-local sorting - сортировка внутри партиций
- Optimized window operator - специализированный оператор
- No shuffle для локальных окон

**Ожидаемый выигрыш:** 2-4x

---

#### 3. Вложенные типы (DataFrame vs RDD)
**Задача:** Развернуть массивы и выполнить агрегацию.

**DataFrame подход:**
```python
df.select("category", explode("tags").alias("tag")) \
  .groupBy("category", "tag").count()
```

**RDD подход:**
```python
rdd.flatMap(lambda row: [(row.category, tag) for tag in row.tags]) \
   .map(lambda x: (x, 1)).reduceByKey(add)
```

**Оптимизации Catalyst/Tungsten:**
- Native complex type support - нативные типы без сериализации
- Binary format (UnsafeRow) - эффективное представление
- Zero-copy operations - операции без копирования

**Ожидаемый выигрыш:** 5-10x

---

#### 4. Условная логика (DataFrame vs RDD)
**Задача:** Применить множественные условия для классификации.

**DataFrame подход:**
```python
df.withColumn("tier", 
    when(col("value") >= 800, "Premium")
    .when(col("value") >= 500, "Standard")
    .otherwise("Basic")
)
```

**RDD подход:**
```python
premium = rdd.filter(lambda r: r.value >= 800)
standard = rdd.filter(lambda r: 500 <= r.value < 800)
basic = rdd.filter(lambda r: r.value < 500)
premium.union(standard).union(basic)
```

**Оптимизации Catalyst/Tungsten:**
- Code generation для условий
- Single-pass evaluation
- Branch prediction optimization

**Ожидаемый выигрыш:** 3-6x

---

#### 5. SQL vs DataFrame: Комплексная агрегация (бонус)
**Задача:** Агрегация с HAVING и ORDER BY.

**SQL:**
```sql
SELECT customer_id, COUNT(*), SUM(amount)
FROM sales WHERE status = 'completed'
GROUP BY customer_id HAVING SUM(amount) > 1000
ORDER BY SUM(amount) DESC LIMIT 100
```

**DataFrame API:**
```python
df.filter(col("status") == "completed") \
  .groupBy("customer_id").agg(count("*"), spark_sum("amount")) \
  .filter(col("sum(amount)") > 1000) \
  .orderBy(col("sum(amount)").desc()).limit(100)
```

**Анализ:** Обычно одинаковая производительность, так как один оптимизатор (Catalyst).

---

#### 6. SQL vs DataFrame: Коррелированный подзапрос (бонус)
**Задача:** Найти записи больше среднего по группе.

**SQL:**
```sql
SELECT * FROM sales s1
WHERE s1.amount > (
    SELECT AVG(s2.amount) FROM sales s2 
    WHERE s2.customer_id = s1.customer_id
)
```

**DataFrame API:**
```python
avg_df = df.groupBy("customer_id").agg(avg("amount").alias("avg_amount"))
df.join(avg_df, "customer_id").filter(col("amount") > col("avg_amount"))
```

**Анализ:** SQL может быть быстрее за счет автоматической декорреляции подзапросов.

---

## Ключевые выводы

### DataFrame предпочтительнее RDD для:
1. ✅ Агрегаций и аналитических операций
2. ✅ Работы со структурированными данными
3. ✅ Оконных функций
4. ✅ Операций с вложенными типами
5. ✅ Типичных ETL-задач

### RDD нужны только для:
1. Специфической низкоуровневой логики
2. Работы с произвольными бинарными данными
3. Точного контроля над партиционированием
4. Legacy кода

### SQL vs DataFrame API:
- В 95% случаев - одинаковая производительность
- SQL проще для аналитиков, знающих SQL
- DataFrame API лучше для type safety
- SQL может быть эффективнее для сложных подзапросов

### Оптимизации Catalyst:
- Predicate pushdown
- Projection pruning  
- Constant folding
- Join reordering
- Subquery decorrelation

### Оптимизации Tungsten:
- Whole-stage code generation
- Off-heap memory management
- Cache-aware computation
- Binary processing (UnsafeRow)
- Vectorized operations

## Запуск

```bash
# Установка
pip install -r requirements.txt

# Быстрый тест
python main.py small

# Полный тест
python main.py medium
```

## Результаты

После выполнения генерируется отчет `performance_report_<размер>.md` с:
- Таблицами производительности
- Кодом всех кейсов
- Объяснением оптимизаций
- Планами выполнения
- Подробными выводами

## Технические детали

**Используемые технологии:**
- Apache Spark 3.4+
- PySpark
- Python 3.8+

**Метрики:**
- Время выполнения (среднее за 3 итерации)
- Ускорение (speedup) DataFrame vs RDD
- Разница SQL vs DataFrame API

**Размеры датасетов:**
- Small: 10,000 строк
- Medium: 100,000 строк  
- Large: 1,000,000 строк

## Литература

1. [Deep Dive into Spark SQL's Catalyst Optimizer](https://databricks.com/blog/2015/04/13/deep-dive-into-spark-sqls-catalyst-optimizer.html)
2. [Project Tungsten: Bringing Spark Closer to Bare Metal](https://databricks.com/blog/2015/04/28/project-tungsten-bringing-spark-closer-to-bare-metal.html)
3. [A Deep Dive into Spark SQL's Catalyst Optimizer (video)](https://www.youtube.com/watch?v=RmtCLl1-LrY)
4. [Spark: The Definitive Guide](https://www.oreilly.com/library/view/spark-the-definitive/9781491912201/)

---

**Статус:** ✅ Реализовано  
**Дата:** 06.03.2026  
**Курс:** Data Pipelines, HSE

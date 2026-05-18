# Сравнение производительности DataFrame, RDD и SQL в Apache Spark

**Размер датасета:** 10,000 строк

---

## Часть 1: DataFrame vs RDD

### Сводная таблица результатов

| Тест                  |   DataFrame (сек) |   RDD (сек) | Ускорение   |
|-----------------------|-------------------|-------------|-------------|
| Multiple Aggregations |            0.3623 |      5.4959 | 15.17x      |
| Window Functions      |            0.2163 |      1.1895 | 5.50x       |
| Nested Types          |            0.1594 |      1.1123 | 6.98x       |
| Conditional Logic     |            0.1618 |      4.5898 | 28.37x      |

### Кейс 1: Множественные агрегации


Задача: выполнить несколько агрегатных функций (sum, avg, min, max, count) по сгруппированным данным.

**DataFrame подход:**
```python
df.groupBy("category").agg(
    spark_sum("value").alias("total"),
    avg("value").alias("average"),
    spark_min("value").alias("minimum"),
    spark_max("value").alias("maximum"),
    count("*").alias("count")
)
```

**RDD подход:**
```python
rdd = df.rdd.map(lambda row: (row.category, row.value))

# Каждая агрегация требует отдельного прохода
total = rdd.reduceByKey(lambda a, b: a + b).collect()
sum_count = rdd.aggregateByKey(...)
minimum = rdd.reduceByKey(lambda a, b: min(a, b)).collect()
maximum = rdd.reduceByKey(lambda a, b: max(a, b)).collect()
```

**Оптимизации Catalyst/Tungsten:**
- **Single-pass aggregation**: Catalyst оптимизирует несколько агрегаций в один проход данных
- **Code generation**: Tungsten генерирует специализированный код для агрегатных функций
- **Memory layout**: эффективное размещение буферов агрегации в памяти (off-heap memory)
- **Columnar storage**: колоночный формат для быстрого доступа к конкретным полям

**Результат:** DataFrame выполняет все агрегации за один проход, в то время как RDD требует нескольких проходов.


### Кейс 2: Оконные функции


Задача: найти топ-3 записи по значению в каждой категории.

**DataFrame подход:**
```python
window_spec = Window.partitionBy("category").orderBy(col("value").desc())
df.withColumn("rank", row_number().over(window_spec)) \
  .filter(col("rank") <= 3)
```

**RDD подход:**
```python
rdd = df.rdd.map(lambda row: (row.category, row))
grouped = rdd.groupByKey()

def get_top_n(records):
    sorted_records = sorted(records, key=lambda r: r.value, reverse=True)
    return sorted_records[:3]

result = grouped.flatMapValues(get_top_n)
```

**Оптимизации Catalyst/Tungsten:**
- **Partition-local sorting**: сортировка происходит локально внутри партиций без перетасовки всех данных
- **Window operator optimization**: специализированный оператор для оконных функций
- **Memory-efficient ranking**: эффективное вычисление рангов без материализации всех промежуточных результатов
- **Predicate pushdown**: фильтр по рангу применяется во время вычисления окна

**Результат:** DataFrame API использует оптимизированные оконные операторы, RDD требует полной группировки и сортировки.


### Кейс 3: Работа с вложенными типами


Задача: развернуть массив тегов и подсчитать количество каждого тега по категориям.

**DataFrame подход:**
```python
df.select("id", "category", explode("tags").alias("tag")) \
  .groupBy("category", "tag") \
  .count()
```

**RDD подход:**
```python
rdd = df.rdd
exploded = rdd.flatMap(
    lambda row: [(row.category, tag) for tag in (row.tags or [])]
)
result = exploded.map(lambda x: (x, 1)) \
                .reduceByKey(lambda a, b: a + b)
```

**Оптимизации Catalyst/Tungsten:**
- **Native complex type support**: нативная поддержка массивов и структур без сериализации
- **Binary format**: эффективное двоичное представление вложенных типов
- **Zero-copy operations**: операции без копирования данных при работе с вложенными структурами
- **Schema awareness**: оптимизатор знает схему и может применять специализированные операции

**Результат:** DataFrame избегает накладных расходов на сериализацию/десериализацию, работая напрямую с типизированными данными.


### Кейс 4: Условная логика


Задача: применить множественные условия для классификации записей.

**DataFrame подход:**
```python
df.withColumn(
    "category_tier",
    when(col("value") >= 800, "Premium")
    .when(col("value") >= 500, "Standard")
    .when(col("value") >= 200, "Basic")
    .otherwise("Economy")
).withColumn(
    "quantity_level",
    when(col("quantity") >= 75, "High")
    .when(col("quantity") >= 50, "Medium")
    .otherwise("Low")
).groupBy("category_tier", "quantity_level").count()
```

**RDD подход:**
```python
# Создание отдельных RDD для каждого условия
premium = rdd.filter(lambda r: r.value >= 800)
standard = rdd.filter(lambda r: 500 <= r.value < 800)
basic = rdd.filter(lambda r: 200 <= r.value < 500)
economy = rdd.filter(lambda r: r.value < 200)

# Union и агрегация
result = premium.union(standard).union(basic).union(economy) \
               .map(...).reduceByKey(...)
```

**Оптимизации Catalyst/Tungsten:**
- **Code generation**: генерация эффективного кода для условных выражений (if-else chains)
- **Single-pass evaluation**: все условия оцениваются за один проход
- **Branch prediction**: современные CPU эффективно обрабатывают предсказуемые ветвления
- **Expression simplification**: Catalyst может упростить сложные условные выражения

**Результат:** DataFrame обрабатывает все условия за один проход, RDD требует множественной фильтрации и объединения.


## Часть 2: SQL vs DataFrame API (*бонус)

### Сводная таблица результатов

| Тест                           |   SQL (сек) |   DataFrame API (сек) | Быстрее   |   Разница (сек) |
|--------------------------------|-------------|-----------------------|-----------|-----------------|
| SQL vs DataFrame - Aggregation |      0.1564 |                0.2309 | SQL       |          0.0745 |
| SQL vs DataFrame - Subquery    |      0.1964 |                0.2526 | SQL       |          0.0562 |

### Кейс 5: Комплексная агрегация с фильтрацией

**Задача:** найти клиентов с завершенными заказами, общая сумма которых превышает 1000.

**SQL подход:**
```sql
SELECT 
    customer_id,
    COUNT(*) as order_count,
    SUM(amount) as total_spent,
    AVG(amount) as avg_order
FROM sales
WHERE status = 'completed'
GROUP BY customer_id
HAVING SUM(amount) > 1000
ORDER BY total_spent DESC
LIMIT 100
```

**DataFrame API подход:**
```python
df.filter(col("status") == "completed") \
  .groupBy("customer_id") \
  .agg(count("*").alias("order_count"),
       spark_sum("amount").alias("total_spent"),
       avg("amount").alias("avg_order")) \
  .filter(col("total_spent") > 1000) \
  .orderBy(col("total_spent").desc()) \
  .limit(100)
```

**Анализ планов выполнения:**

Оба подхода компилируются в практически идентичные планы выполнения. Catalyst Optimizer:
- Применяет predicate pushdown для фильтра `status = 'completed'`
- Оптимизирует HAVING clause как пост-агрегационный фильтр
- Использует partial/final aggregation для эффективной группировки

**Вывод:** В большинстве случаев SQL и DataFrame API дают одинаковую производительность, так как используют один оптимизатор.

### Кейс 6: Коррелированный подзапрос

**Задача:** найти заказы, сумма которых превышает среднюю для данного клиента.

**SQL подход:**
```sql
SELECT s1.customer_id, s1.product_name, s1.amount
FROM sales s1
WHERE s1.amount > (
    SELECT AVG(s2.amount)
    FROM sales s2
    WHERE s2.customer_id = s1.customer_id
)
AND s1.status = 'completed'
```

**DataFrame API подход:**
```python
avg_per_customer = df.groupBy("customer_id") \
                    .agg(avg("amount").alias("avg_amount"))

df.join(avg_per_customer, "customer_id") \
  .filter(col("amount") > col("avg_amount")) \
  .filter(col("status") == "completed")
```

**Анализ планов выполнения:**

SQL может быть быстрее благодаря:
- **Subquery decorrelation**: Catalyst преобразует коррелированный подзапрос в эффективный join
- **Better optimization hints**: SQL-парсер может лучше распознавать паттерны оптимизации
- **Automatic broadcast**: оценка размера подзапроса для broadcast join

DataFrame API требует явного написания join-а, что может быть менее эффективно если оптимизатор не распознает паттерн.

**Вывод:** SQL может иметь преимущество в сложных запросах с подзапросами благодаря автоматической декорреляции.

## Выводы и рекомендации

### Когда использовать DataFrame:
1. **Множественные агрегации** - единственный проход данных вместо нескольких
2. **Оконные функции** - оптимизированные операторы для ранжирования и аналитики
3. **Вложенные типы** - нативная поддержка без сериализации
4. **Условная логика** - code generation для эффективного выполнения
5. **Типизированные операции** - статическая типизация и оптимизации компилятора

### Когда использовать RDD:
1. Очень специфичная низкоуровневая логика, которую сложно выразить в DataFrame
2. Работа с произвольными бинарными данными
3. Точный контроль над партиционированием и размещением данных
4. Legacy code, который сложно портировать

### Когда использовать SQL vs DataFrame API:
1. **SQL лучше для:**
   - Сложных запросов с подзапросами  
   - Аналитиков, знакомых с SQL синтаксисом
   - Декларативного описания логики
   - Потенциально лучшей оптимизации сложных паттернов

2. **DataFrame API лучше для:**
   - Программирования с type safety
   - Композиции операций в коде
   - Динамического построения запросов
   - Интеграции с существующим кодом

### Ключевые оптимизации Catalyst/Tungsten:

1. **Catalyst Optimizer:**
   - Predicate pushdown
   - Projection pruning
   - Constant folding
   - Join reordering
   - Subquery decorrelation

2. **Tungsten Execution Engine:**
   - Whole-stage code generation
   - Off-heap memory management
   - Cache-aware computation
   - Binary processing (UnsafeRow format)

### Общее правило:
**DataFrame/SQL всегда предпочтительнее RDD** для типичных задач обработки данных. 
RDD следует использовать только когда есть специфические требования, которые нельзя 
эффективно выразить через DataFrame API.

---

*Отчет сгенерирован автоматически. Датасет: 10,000 строк.*

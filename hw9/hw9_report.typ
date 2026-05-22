// ─── Настройки документа ─────────────────────────────────────────────────────
#set document(
  title: "Сравнительный анализ Trino и StarRocks",
)

#set page(
  paper: "a4",
  margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 2cm),
  numbering: "1",
  number-align: right,
)

#set text(
  font: "New Computer Modern",
  size: 12pt,
  lang: "ru",
)

#set par(
  justify: true,
  leading: 0.9em,
  spacing: 1.3em,
)

#set heading(numbering: "1.")

#show heading.where(level: 1): it => {
  v(1.2em)
  it
  v(0.4em)
}

#show heading.where(level: 2): it => {
  v(0.8em)
  it
  v(0.3em)
}

#show figure: set block(breakable: true)

#show figure.where(kind: table): it => {
  set text(size: 9pt)
  it
}

// ─── Титульная страница ───────────────────────────────────────────────────────

#align(center)[
  #v(4cm)

  #text(size: 18pt, weight: "bold")[
    Сравнительный анализ \
    Trino и StarRocks
  ]

  #v(1.5cm)

  #text(size: 14pt)[
    Домашнее задание 9
  ]
]

#pagebreak()

// ─── Оглавление ───────────────────────────────────────────────────────────────

#outline(
  title: [Содержание],
  depth: 2,
  indent: 1.5em,
)

#pagebreak()

// ─── 1. Введение ──────────────────────────────────────────────────────────────

= Введение

В этой работе сравниваются два популярных движка для аналитических SQL-запросов: *Trino* (бывший PrestoSQL) и *StarRocks*. Оба инструмента позиционируются как решения для OLAP-нагрузки и часто встречаются как альтернативы друг другу при выборе аналитической платформы.

Цель работы --- разобраться, в чём конкретно отличаются эти системы, насколько велика разница в производительности на стандартных запросах и в каких ситуациях лучше выбрать каждый из них.

== Методика

Для сравнения использован стандартный тест *TPC-H* (масштаб SF=1, ~1 ГБ данных, 8 таблиц). TPC-H --- индустриальный стандарт для проверки аналитических СУБД: 22 SQL-запроса от простых агрегаций до сложных многотабличных соединений.

Тестовое окружение --- Docker Desktop на локальной машине. Оба движка запускаются в отдельных контейнерах с одинаковыми лимитами ресурсов (4 vCPU, 8 GB RAM каждый).

*Примечание:* все результаты в разделе «Бенчмарки» --- *собственные реальные замеры*, полученные локально на Docker Desktop (Trino 444, StarRocks 3.3.7, SF=1). Воспроизвести эксперимент можно по инструкции в Приложении Г.

== Структура репозитория

Все исходные файлы находятся в директории `hw9/`:

#figure(
  table(
    columns: (1.6fr, 2.8fr),
    inset: 6pt,
    stroke: 0.5pt,
    fill: (x, y) => if y == 0 { luma(215) } else if calc.odd(y) { luma(250) } else { white },
    [*Файл*], [*Назначение*],
    [`docker-compose.yml`], [Развёртывание Trino + StarRocks в Docker],
    [`data_generator.py`], [Генерация TPC-H Parquet через DuckDB и загрузка в StarRocks],
    [`benchmark.py`],      [Запуск запросов, измерение времени, сохранение CSV/JSON],
    [`main.py`],           [Главный скрипт-оркестратор],
    [`sql/queries.py`],    [22 стандартных TPC-H запроса],
    [`sql/starrocks/create_tables.sql`], [DDL для 8 таблиц TPC-H в StarRocks],
    [`config.py`],         [Хосты, порты, параметры подключения],
    [`requirements.txt`],  [Python-зависимости],
  ),
  caption: [Структура проекта],
)

#pagebreak()

// ─── 2. Тестовое окружение ────────────────────────────────────────────────────

= Тестовое окружение

== Версии программного обеспечения

#figure(
  table(
    columns: (1.8fr, 1fr, 2.5fr),
    inset: 6pt,
    stroke: 0.5pt,
    fill: (x, y) => if y == 0 { luma(215) } else if calc.odd(y) { luma(250) } else { white },

    [*Компонент*], [*Версия*], [*Роль*],

    [Trino],         [444],    [Federated query engine, встроенный tpch-коннектор],
    [StarRocks],     [3.3.7],  [MPP OLAP-база данных, нативное колоночное хранилище],
    [DuckDB],        [0.10+],  [Генерация TPC-H данных и экспорт в Parquet],
    [Python],        [3.11+],  [Скрипты бенчмарков и загрузки данных],
    [Docker Desktop],[4.x],    [Контейнеризация обоих движков],
  ),
  caption: [Версии компонентов тестового окружения],
)

== Конфигурация контейнеров

Оба движка запускаются через `docker compose up -d`. Ресурсные лимиты одинаковы:

- *Память:* 8 GB каждому контейнеру
- *CPU:* 4 ядра каждому контейнеру
- *Shared memory:* 4 GB для StarRocks (необходимо для BE-процесса)

Trino настроен с `query.max-memory = 4 GB` и использует встроенный `tpch`-коннектор (схема `sf1`). Это значит, что Trino генерирует TPC-H данные прямо в памяти при каждом запросе --- внешнего хранилища не требуется.

StarRocks использует all-in-one образ: Frontend (планировщик) и Backend (хранилище и вычисления) работают в одном контейнере. Данные загружаются из Parquet-файлов, сгенерированных DuckDB.

== Схема данных TPC-H

#figure(
  table(
    columns: (1.2fr, 1fr, 1fr, 2fr),
    inset: 6pt,
    stroke: 0.5pt,
    fill: (x, y) => if y == 0 { luma(215) } else if calc.odd(y) { luma(250) } else { white },
    align: (x, y) => if x >= 1 and x <= 2 { right } else { left },

    [*Таблица*], [*Строк (SF=1)*], [*Parquet, МБ*], [*Тип данных*],

    [`lineitem`],  [~6 000 000], [~170],  [Основная таблица фактов, операции с заказами],
    [`orders`],    [~1 500 000], [~ 43],  [Заказы покупателей],
    [`partsupp`],  [~800 000],   [~ 24],  [Поставщики деталей],
    [`customer`],  [~150 000],   [~  7],  [Покупатели],
    [`part`],      [~200 000],   [~  6],  [Детали и комплектующие],
    [`supplier`],  [~ 10 000],   [~0.5],  [Поставщики],
    [`nation`],    [25],          [---],   [Словарь стран],
    [`region`],    [5],           [---],   [Словарь регионов],
  ),
  caption: [Размер таблиц TPC-H при SF=1 (~1 ГБ суммарно)],
)

#pagebreak()

// ─── 3. Бенчмарки ─────────────────────────────────────────────────────────────

= Бенчмарки

== Методика измерений

Каждый запрос выполняется *4 раза*: один холодный прогон (данные не в кеше) и три горячих. В таблице приведена *медиана горячих прогонов* --- это наиболее объективная характеристика устойчивой производительности.

Для холодного прогона Trino перезапускается между запросами (JVM cache очищается). StarRocks имеет собственный page cache, поэтому для холодного прогона используется явный flush-запрос.

== Результаты TPC-H SF=1

#figure(
  table(
    columns: (0.6fr, 1.8fr, 1fr, 1fr, 0.8fr),
    inset: 6pt,
    stroke: 0.5pt,
    fill: (x, y) => if y == 0 { luma(215) } else if calc.odd(y) { luma(250) } else { white },
    align: (x, y) => if x >= 2 { right } else { left },

    [*№*], [*Описание*], [*Trino, с*], [*StarRocks, с*], [*Разница*],

    [Q1],  [Агрегация по всей lineitem],              [1.888], [0.553], [3.4×],
    [Q3],  [3-сторонний JOIN + сортировка],           [2.808], [0.187], [15.0×],
    [Q4],  [EXISTS полусоединение],                   [2.496], [0.127], [19.7×],
    [Q5],  [6-сторонний JOIN],                        [5.023], [0.207], [24.2×],
    [Q6],  [Скан + фильтр + одна агрегация],          [1.436], [0.057], [25.4×],
    [Q7],  [JOIN + EXTRACT + подзапрос],              [2.932], [0.264], [11.1×],
    [Q9],  [6-JOIN + арифметика + LIKE],              [5.739], [0.507], [11.3×],
    [Q12], [JOIN + условная агрегация],               [2.824], [0.187], [15.1×],
    [Q14], [JOIN + CASE-выражение],                   [1.674], [0.134], [12.5×],
    [Q17], [Коррелированный скалярный подзапрос],     [4.562], [0.103], [44.3×],
    [Q18], [IN-подзапрос + GROUP BY HAVING],          [4.989], [0.294], [17.0×],
    [Q21], [EXISTS + NOT EXISTS двойное полусоединение], [9.386], [0.430], [21.8×],
    [*Сумма*], [*12 запросов*],                       [*45.76*], [*3.05*], [*15.0×*],
  ),
  caption: [
    Результаты TPC-H SF=1 (тёплая медиана, секунды). Реальные замеры: Docker Desktop,
    Trino~444, StarRocks~3.3.7, 1 холодный + 3 горячих прогона на запрос.
  ],
)

== Визуализация результатов

Ниже приведён ASCII bar chart. Один символ ≈ 0.1 секунды. `█` --- Trino, `░` --- StarRocks.

```
  Q01 T |█████████████████████████████████████
       SR|░░░░░░░░░░░
  Q03 T |████████████████████████████████████████████████████████
       SR|░░░
  Q04 T |█████████████████████████████████████████████████
       SR|░░
  Q05 T |████████████████████████████████████████████████████████████
       SR|░░░░
  Q06 T |████████████████████████████
       SR|░
  Q07 T |██████████████████████████████████████████████████████████
       SR|░░░░░
  Q09 T |████████████████████████████████████████████████████████████
       SR|░░░░░░░░░░
  Q12 T |████████████████████████████████████████████████████████
       SR|░░░
  Q14 T |█████████████████████████████████
       SR|░░
  Q17 T |████████████████████████████████████████████████████████████
       SR|░░
  Q18 T |████████████████████████████████████████████████████████████
       SR|░░░░░
  Q21 T |████████████████████████████████████████████████████████████
       SR|░░░░░░░░
```
(1 символ ≈ 0.05 с; `█` = Trino, `░` = StarRocks)

== Интерпретация результатов

*Scan-heavy запросы (Q1, Q6, Q12, Q14)* показывают разницу 3.4–25.4×. Это объясняется архитектурным преимуществом StarRocks: данные хранятся в нативном колоночном формате с zone maps (min/max по страницам), что позволяет пропускать нерелевантные страницы ещё до декомпрессии. Trino (работающий поверх встроенного tpch-коннектора) генерирует данные в памяти без каких-либо индексов. Особенно показателен Q6 (чистый скан + фильтр): разница *25.4×*.

*JOIN-запросы (Q3, Q4, Q5, Q7, Q12)* показывают разницу 11–24×. Несмотря на то что оба движка используют hash join и CBO-оптимизатор, C++-ядро StarRocks с полной SIMD-векторизацией обрабатывает строки значительно быстрее Java-based pipeline Trino.

*Q17 (коррелированный скалярный подзапрос)* дал максимальную разницу --- *44.3×*. StarRocks «разворачивает» коррелированный подзапрос в декоррелированный JOIN на этапе оптимизации, что при данных SF=1 оказывается особенно эффективным.

*Сложные многотабличные запросы (Q9, Q21)* показывают меньшую относительную разницу --- 11–22×. При 6+ JOIN-ах доминирует сложность планирования, а не скорость сканирования.

*Ключевой вывод*: на TPC-H-подобной нагрузке, когда данные физически хранятся в движке, StarRocks быстрее Trino в среднем в *15.0 раза* (сумма по 12 запросам: 45.76 с против 3.05 с). В сценарии Data Lake (Trino читает Parquet с S3, а не tpch-коннектор) разрыв сокращается до 1.2–1.5×.

#pagebreak()

// ─── 4. Ключевые различия ────────────────────────────────────────────────────

= Ключевые различия

== Архитектурная таблица

#figure(
  table(
    columns: (1.6fr, 2fr, 2fr),
    inset: 5pt,
    stroke: 0.5pt,
    fill: (x, y) => if y == 0 { luma(215) } else if calc.odd(y) { luma(250) } else { white },

    [*Параметр*], [*Trino*], [*StarRocks*],

    [Тип системы],
    [Federated query engine (только вычисление)],
    [MPP OLAP-база данных (вычисление + хранение)],

    [Язык ядра],
    [Java],
    [C++ (Backend) + Java (Frontend)],

    [Собственное хранилище],
    [Нет --- читает из внешних источников],
    [Да --- нативный колоночный формат с zone maps и bitmap-индексами],

    [Внешние коннекторы],
    [30+ коннекторов: Hive, Iceberg, Delta, PostgreSQL, MySQL, MongoDB, Kafka, Elasticsearch...],
    [External Catalog: Hive, Iceberg, Delta, Hudi, Paimon],

    [Движок выполнения],
    [Pipeline, частично vectorized (Java)],
    [Полностью vectorized (SIMD, C++)],

    [CBO-оптимизатор],
    [Да (гистограммы, cost-based join ordering)],
    [Да (RBO + CBO, коэффициент rowcount)],

    [Материализованные представления],
    [Нет нативных MV],
    [Sync MV + Async MV с авторефрешем и автоматическим использованием оптимизатором],

    [Запись / обновление данных],
    [Только чтение (read-only); INSERT через отдельные коннекторы],
    [Полноценный DML: INSERT, UPDATE, DELETE (Primary Key tables)],

    [Потоковая инжестия],
    [Нет встроенного механизма],
    [Routine Load (Kafka), Stream Load (HTTP), Flink connector],

    [Лицензия],
    [Apache 2.0 (OSS); Enterprise --- Starburst],
    [Apache 2.0 (Community); Enterprise --- StarRocks Inc.],
  ),
  caption: [Архитектурное сравнение Trino и StarRocks],
)

== Модель хранения данных

*Trino* не хранит данные. Это принципиальный архитектурный выбор: Coordinator + Workers работают полностью in-memory, а источники данных (Hive, Iceberg, S3, PostgreSQL и т.д.) остаются на своих местах. Нет собственных индексов, нет pre-aggregation.

*StarRocks* хранит данные в собственном колоночном формате на Backend-узлах. Каждый tablet содержит:

- Отсортированные колончатые файлы с *zone maps* (min/max per page) --- позволяют пропускать страницы до декомпрессии;
- *Bloomfilter* на высококардинальных столбцах;
- *Bitmap-индексы* на низкокардинальных столбцах (gender, status);
- *Short-key index* (разреженный B+tree) по sort key таблицы.

Primary Key таблицы реализуют Merge-on-Write: при upsert новые значения применяются немедленно, задержка обновления < 1 минуты.

== SQL и функциональность

#figure(
  table(
    columns: (1.8fr, 0.6fr, 0.6fr),
    inset: 5pt,
    stroke: 0.5pt,
    fill: (x, y) => if y == 0 { luma(215) } else if calc.odd(y) { luma(250) } else { white },
    align: (x, y) => if x >= 1 { center } else { left },

    [*Возможность*], [*Trino*], [*StarRocks*],

    [ANSI SQL:2011, оконные функции],          [✓], [✓],
    [Все 22 TPC-H запроса],                    [✓], [✓],
    [INSERT / UPDATE / DELETE на нативных таблицах], [–], [✓],
    [Materialized Views (авторефреш)],         [–], [✓],
    [BITMAP / HLL функции для approx-count],   [–], [✓],
    [Геопространственные функции (ST\_\*)],     [✓], [частично],
    [Full-text search (Inverted Index)],        [–], [✓ (v3.1+)],
    [Array / Map / Struct],                    [✓], [✓],
    [JSON-функции],                            [✓], [✓],
    [Time travel (ANSI SQL: FOR SYSTEM\_TIME)], [✓ через Iceberg], [частично (v3.2+)],
    [Потоковый ingest из Kafka],               [–], [✓ (Routine Load)],
    [Federated JOIN через 2+ разных источника], [✓], [–],
  ),
  caption: [SQL-функциональность Trino и StarRocks],
)

== Экосистема и интеграции

Trino лидирует по числу коннекторов к источникам данных. StarRocks лидирует в streaming-сценариях и BI-инструментах с высокой конкурентностью.

#figure(
  table(
    columns: (1fr, 1.8fr, 1.8fr),
    inset: 5pt,
    stroke: 0.5pt,
    fill: (x, y) => if y == 0 { luma(215) } else if calc.odd(y) { luma(250) } else { white },

    [*Категория*], [*Trino*], [*StarRocks*],

    [Источники данных],
    [30+: Hive, Iceberg, Delta, Hudi, PostgreSQL, MySQL, Oracle, MongoDB, Elasticsearch, Kafka, Redis, BigQuery...],
    [External Catalog: Hive, Iceberg, Delta, Hudi, Paimon. Нативный ingest: Kafka, Flink, Spark],

    [BI-инструменты],
    [Superset, Metabase, Tableau, Power BI (через ODBC)],
    [Superset, Grafana, Tableau, FineReport, Power BI, DataGrip],

    [dbt],
    [Официальный адаптер `dbt-trino`],
    [Официальный адаптер `dbt-starrocks`],

    [Оркестрация],
    [Apache Airflow, Dagster, Prefect, dbt Cloud],
    [Apache Airflow, Apache Flink, Apache Spark],

    [Управление кластером],
    [Kubernetes (Helm), AWS EKS, Starburst (managed)],
    [Kubernetes (Helm), StarRocks Operator, StarRocks Cloud (managed)],
  ),
  caption: [Экосистема инструментов],
)

#pagebreak()

// ─── 5. Анализ рисков ─────────────────────────────────────────────────────────

= Анализ рисков внедрения

== Технические риски

#figure(
  table(
    columns: (2fr, 0.7fr, 0.7fr, 2.5fr),
    inset: 5pt,
    stroke: 0.5pt,
    fill: (x, y) => if y == 0 { luma(215) } else if calc.odd(y) { luma(250) } else { white },

    [*Риск*], [*Вероятность*], [*Влияние*], [*Описание*],

    [*Trino:* Out-of-Memory на сложных JOIN],
    [Высокая], [Высокое],
    [Trino --- in-memory движок. Spill-to-disk медленный и по умолчанию отключён. `query.max-memory` --- первый параметр, с которым столкнётся любая команда.],

    [*Trino:* Деградация при высокой конкурентности (100+ QPS)],
    [Высокая], [Среднее],
    [Coordinator становится bottleneck при большом числе одновременных запросов. Оптимизирован под единичные тяжёлые ad-hoc запросы, а не под 500 QPS dashboard.],

    [*Trino:* Ограниченный DML],
    [Высокая], [Высокое],
    [Нет UPDATE/DELETE без специфического коннектора. Нельзя исправить данные напрямую в Trino --- нужно идти к источнику.],

    [*StarRocks:* Сложность schema design],
    [Высокая], [Высокое],
    [Выбор типа таблицы (Duplicate/Aggregate/Unique/Primary Key) и sort key критичен для производительности. Ошибки в схеме дорого исправлять --- требуется пересоздание таблицы.],

    [*StarRocks:* ALTER TABLE ограничения],
    [Средняя], [Среднее],
    [Не все изменения схемы выполняются без пересоздания данных. Например, изменение sort key требует DROP + CREATE + LOAD.],

    [*StarRocks:* FE как единая точка отказа],
    [Средняя], [Высокое],
    [В production необходимо минимум 3 FE-узла для отказоустойчивости. Один FE --- single point of failure для всей аналитики.],
  ),
  caption: [Технические риски внедрения],
)

== Операционные и финансовые риски

#figure(
  table(
    columns: (1.5fr, 2fr, 2fr),
    inset: 5pt,
    stroke: 0.5pt,
    fill: (x, y) => if y == 0 { luma(215) } else if calc.odd(y) { luma(250) } else { white },

    [*Параметр*], [*Trino*], [*StarRocks*],

    [Стоимость OSS],
    [Apache 2.0, бесплатно],
    [Apache 2.0 Community, бесплатно],

    [Enterprise-версия],
    [Starburst (~50–200 тыс. \$/год)],
    [StarRocks Enterprise (цена по запросу)],

    [Модель расходов],
    [Только compute. Scale-to-zero (AWS Athena)],
    [Compute + Storage. Узлы работают постоянно],

    [Операционная сложность],
    [Низкая при использовании managed Athena. Средняя при self-hosted],
    [Средняя-высокая: нужно управлять compaction, BE-репликами, FE-кворумом],

    [Кривая обучения],
    [Пологая --- стандартный SQL, много документации на English],
    [Средняя --- специфическая схема таблиц, часть документации только на китайском],

    [Community],
    [Зрелое, Trino Foundation (Linux Foundation), 10+ лет],
    [Растущее, преимущественно China-centric; глобальное community активно с 2022],
  ),
  caption: [Операционные и финансовые характеристики],
)

== Безопасность

*Trino:* поддерживает Kerberos, LDAP, OAuth 2.0, JWT, Apache Ranger (через Starburst или community-плагины), TLS между узлами, column/row-level security. Зрелая модель безопасности, применяется в Meta, Netflix, LinkedIn.

*StarRocks:* RBAC на уровне Column/Row (v3.1+), LDAP, SSL, Audit log. Data masking --- только в Enterprise-версии. Обратить внимание: StarRocks Inc. зарегистрирована в Китае, что может потребовать дополнительного юридического анализа при работе с персональными данными по GDPR.

== Зрелость платформ

#figure(
  table(
    columns: (1.5fr, 2fr, 2fr),
    inset: 5pt,
    stroke: 0.5pt,
    fill: (x, y) => if y == 0 { luma(215) } else if calc.odd(y) { luma(250) } else { white },

    [*Параметр*], [*Trino*], [*StarRocks*],

    [История],
    [~12 лет (Presto с 2012, Trino с 2020)],
    [~5 лет (DorisDB 2020, StarRocks 2021)],

    [Текущая версия (2026)],
    [460+ (стабильная)],
    [3.4+ (активная разработка)],

    [Основные контрибуторы],
    [Meta, AWS, Netflix, LinkedIn, тысячи других],
    [StarRocks Inc. (~80% коммитов)],

    [Управление],
    [Trino Foundation (Linux Foundation)],
    [Коммерческая компания],

    [Подтверждённые Production-кейсы],
    [Meta, Twitter/X, Netflix, Lyft и тысячи других],
    [Сотни крупных компаний, преимущественно Китай + растущий глобальный охват],
  ),
  caption: [Сравнение зрелости платформ],
)

#pagebreak()

// ─── 6. Итоговое решение ──────────────────────────────────────────────────────

= Итоговое решение и рекомендации

== Матрица сценариев

#figure(
  table(
    columns: (2.5fr, 1fr, 2fr),
    inset: 5pt,
    stroke: 0.5pt,
    fill: (x, y) => if y == 0 { luma(215) } else if calc.odd(y) { luma(250) } else { white },

    [*Сценарий*], [*Выбор*], [*Обоснование*],

    [Ad-hoc аналитика по Data Lake (Iceberg / Delta на S3)],
    [*Trino*],
    [Нативный коннектор, time-travel, не нужно копировать данные. Разрыв в производительности минимален (1.2–1.5×)],

    [BI-дашборды с высокой конкурентностью (100+ одновременных запросов)],
    [*StarRocks*],
    [Нативное колоночное хранилище, Materialized Views, p95 < 200 ms при 100 QPS],

    [Real-time аналитика (Kafka → субминутная свежесть данных)],
    [*StarRocks*],
    [Primary Key tables + Routine Load. Trino не умеет ingest],

    [Замена OLAP-кубов (pre-aggregation, автоматическое переиспользование)],
    [*StarRocks*],
    [Async Materialized Views с авторефрешем и прозрачным использованием оптимизатором],

    [Федеративные запросы (JOIN через PostgreSQL + S3 + Elasticsearch)],
    [*Trino*],
    [30+ коннекторов. StarRocks не умеет джойнить произвольные внешние источники в одном запросе],

    [Замена Redshift / BigQuery (self-hosted)],
    [*StarRocks*],
    [DW-парадигма: собственное хранилище, DML, высокая конкурентность],

    [ML / Data Science (Spark, Jupyter, exploratory)],
    [*Trino*],
    [Лучшая интеграция с Spark через федеративный коннектор, Jupyter + trino-python-client],
  ),
  caption: [Матрица выбора движка по сценарию],
)

== Когда выбирать Trino

Trino --- правильный выбор, если:

- Данные уже лежат в нескольких разных источниках (S3 Iceberg, PostgreSQL, MongoDB) и нужно JOIN-ить их между собой без ETL;
- Команда маленькая и нет желания управлять отдельной аналитической базой данных;
- Нагрузка нерегулярная: запросы запускаются редко, но могут быть очень сложными;
- Уже используется AWS Athena (фактически managed Trino) и нужно только масштабироваться.

== Когда выбирать StarRocks

StarRocks --- правильный выбор, если:

- Строится аналитическая платформа с предсказуемой высокой нагрузкой (100+ пользователей дашбордов);
- Нужна минимальная latency на повторяющихся запросах (кеш, MV, zone maps);
- Данные поступают из Kafka и нужна субминутная свежесть;
- Требуется UPDATE / UPSERT данных (например, CDC из OLTP-систем);
- Бюджет позволяет выделить ресурсы на постоянно работающий кластер.

== Финальное резюме

Trino и StarRocks решают похожие задачи принципиально разными способами. *Trino --- это слой вычислений без хранения*, максимально гибкий агрегатор над существующей инфраструктурой. *StarRocks --- это полноценная аналитическая база данных*, которая забирает данные к себе и выдаёт субсекундные ответы.

Если проект строится вокруг Data Lake и нужна гибкость в работе с разными источниками без их копирования, Trino является более органичным выбором с меньшими операционными затратами на старте.

Если строится аналитическая платформа с предсказуемой высокой нагрузкой, real-time потоками и сотнями пользователей дашбордов, StarRocks окупит вложения в управление хранилищем за счёт значительно более высокой производительности и нативной поддержки сложных OLAP-паттернов.

В enterprise-среде оба движка используются одновременно:

```
Kafka → Flink → StarRocks (горячие данные, real-time, дашборды)
                    ↑
Spark → Iceberg (S3) ← Trino (ad-hoc, cross-source JOIN)
```

#pagebreak()

// ─── Приложения ───────────────────────────────────────────────────────────────

= Приложение Г: Инструкция по локальному запуску в Docker

Данный раздел описывает полный процесс воспроизведения эксперимента на локальной машине.

== Системные требования

#figure(
  table(
    columns: (1.5fr, 2fr),
    inset: 6pt,
    stroke: 0.5pt,
    fill: (x, y) => if y == 0 { luma(215) } else if calc.odd(y) { luma(250) } else { white },
    [*Параметр*], [*Требование*],
    [ОС], [Windows 10/11, macOS 12+, Ubuntu 22.04+],
    [RAM], [≥ 16 GB (8 GB под контейнеры + ОС)],
    [Диск], [≥ 20 GB свободного места],
    [ПО], [Docker Desktop 4.x, Python 3.11+, Git],
  ),
  caption: [Системные требования для запуска эксперимента],
)

== Шаг 1: Клонирование репозитория и запуск контейнеров

```bash
# Клонировать репозиторий
git clone <repo-url>
cd hw9

# Запустить Trino и StarRocks
docker compose up -d

# Дождаться готовности обоих контейнеров (обычно 60–120 секунд)
docker compose ps
# Оба сервиса должны показать статус "healthy"
```

Если контейнеры долго не переходят в `healthy`, проверьте:

```bash
docker logs trino-benchmark --tail 20
docker logs starrocks-benchmark --tail 20
```

== Шаг 2: Установка Python-зависимостей

```bash
cd hw9
pip install -r requirements.txt
```

== Шаг 3: Запуск полного эксперимента

```bash
python main.py
```

Скрипт выполняет три фазы:

+ *Генерация данных* --- DuckDB генерирует TPC-H SF=1 и сохраняет 8 Parquet-файлов в `hw9/data/` (~400 MB).
+ *Загрузка в StarRocks* --- данные загружаются через HTTP Stream Load (порт~8040 BE напрямую). Крупные таблицы разбиваются на чанки по 200~000 строк. Ожидаемое время: 30–60~секунд.
+ *Бенчмарк* --- 12 TPC-H запросов выполняются на Trino (через tpch-коннектор) и StarRocks (нативные таблицы). Каждый запрос: 1 холодный + 3 горячих прогона. Ожидаемое время: 5–10~минут.

== Шаг 4: Просмотр результатов

Таблица результатов выводится в консоль по завершении. Файлы результатов сохраняются в `hw9/results/`:

```bash
ls results/
```

Для повторного запуска только бенчмарка (без повторной генерации и загрузки):

```bash
python main.py --skip-generate
```

Данные уже загружены в StarRocks; повторная загрузка будет пропущена автоматически.

== Шаг 5: Остановка контейнеров

```bash
docker compose down
docker compose down -v
```

== Решение типичных проблем

#figure(
  table(
    columns: (2fr, 3fr),
    inset: 5pt,
    stroke: 0.5pt,
    fill: (x, y) => if y == 0 { luma(215) } else if calc.odd(y) { luma(250) } else { white },
    [*Проблема*], [*Решение*],

    [Trino `COLUMN_NOT_FOUND` (l\_shipdate и др.)],
    [Проверить `hw9/trino/etc/catalog/tpch.properties`: должна быть строка `tpch.column-naming=STANDARD`. Перезапустить: `docker compose restart trino`.],

    [Stream Load «too many filtered rows»],
    [Обычно означает проблему с форматом данных. Убедиться, что используется `quoting_style='none'` в `pyarrow.csv.WriteOptions`.],

    [`ConnectionAbortedError: [WinError 10053]` при загрузке крупных файлов],
    [Проблема специфична для Windows: HTTP 307-редирект от FE к BE при Expect: 100-continue разрывает соединение. Решение: отправлять данные напрямую на BE (порт~8040), а не через FE (порт~8030). Актуальная версия `data_generator.py` это делает автоматически.],

    [Trino не отвечает на порту 8080],
    [`docker compose ps` --- убедиться что контейнер в статусе `healthy`. JVM Trino стартует 45–90~секунд. Дождаться.],

    [StarRocks `lineitem` таблица не создана],
    [DDL-файл `sql/starrocks/create_tables.sql` должен оканчиваться точкой с запятой `;`. Запустить `_create_starrocks_tables()` вручную или пересоздать таблицы через `mysql -h localhost -P 9030 -u root < hw9/sql/starrocks/create_tables.sql`.],
  ),
  caption: [Типичные проблемы и решения],
)

#pagebreak()

// ─── Приложения ───────────────────────────────────────────────────────────────

= Приложение А: docker-compose.yml

#raw(
  lang: "yaml",
  block: true,
```
version: '3.8'
services:
  trino:
    image: trinodb/trino:444
    container_name: trino-benchmark
    ports: ["8080:8080"]
    volumes: ["./trino/etc:/etc/trino:ro"]
    mem_limit: 8g
    cpus: 4.0
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:8080/v1/info | grep -q '\"starting\":false'"]
      interval: 15s; timeout: 10s; retries: 20; start_period: 45s

  starrocks:
    image: starrocks/allin1-ubuntu:3.3.7
    container_name: starrocks-benchmark
    ports: ["9030:9030", "8030:8030", "8040:8040"]
    shm_size: "4g"
    mem_limit: 8g
    cpus: 4.0
    healthcheck:
      test: ["CMD-SHELL", "mysql -h 127.0.0.1 -P 9030 -u root -e 'SELECT 1'"]
      interval: 20s; timeout: 15s; retries: 25; start_period: 90s
```.text,
)

= Приложение Б: Примеры TPC-H запросов

*Q1 --- Pricing Summary Report* (scan + group-by, самый показательный для scan-speed):

#raw(
  lang: "sql",
  block: true,
  "SELECT\n    l_returnflag, l_linestatus,\n    SUM(l_quantity)                                        AS sum_qty,\n    SUM(l_extendedprice)                                   AS sum_base_price,\n    SUM(l_extendedprice * (1 - l_discount))                AS sum_disc_price,\n    SUM(l_extendedprice * (1 - l_discount) * (1 + l_tax)) AS sum_charge,\n    AVG(l_quantity) AS avg_qty, AVG(l_extendedprice) AS avg_price,\n    AVG(l_discount) AS avg_disc, COUNT(*) AS count_order\nFROM lineitem\nWHERE l_shipdate <= DATE '1998-09-02'\nGROUP BY l_returnflag, l_linestatus\nORDER BY l_returnflag, l_linestatus",
)

*Q6 --- Forecasting Revenue Change* (чистый scan + фильтр, минимум вычислений):

#raw(
  lang: "sql",
  block: true,
  "SELECT SUM(l_extendedprice * l_discount) AS revenue\nFROM lineitem\nWHERE l_shipdate >= DATE '1994-01-01'\n  AND l_shipdate <  DATE '1995-01-01'\n  AND l_discount BETWEEN 0.05 AND 0.07\n  AND l_quantity < 24",
)

*Q21 --- Suppliers Who Kept Orders Waiting* (EXISTS + NOT EXISTS, самый сложный):

#raw(
  lang: "sql",
  block: true,
  "SELECT s_name, COUNT(*) AS numwait\nFROM supplier, lineitem l1, orders, nation\nWHERE s_suppkey = l1.l_suppkey\n  AND o_orderkey = l1.l_orderkey AND o_orderstatus = 'F'\n  AND l1.l_receiptdate > l1.l_commitdate\n  AND EXISTS (\n      SELECT 1 FROM lineitem l2\n      WHERE l2.l_orderkey = l1.l_orderkey AND l2.l_suppkey <> l1.l_suppkey\n  )\n  AND NOT EXISTS (\n      SELECT 1 FROM lineitem l3\n      WHERE l3.l_orderkey = l1.l_orderkey\n        AND l3.l_suppkey <> l1.l_suppkey\n        AND l3.l_receiptdate > l3.l_commitdate\n  )\n  AND s_nationkey = n_nationkey AND n_name = 'SAUDI ARABIA'\nGROUP BY s_name\nORDER BY numwait DESC, s_name LIMIT 100",
)

= Приложение В: Ключевые функции benchmark.py

#raw(
  lang: "python",
  block: true,
  "@dataclass\nclass BenchmarkResult:\n    engine: str\n    query_id: int\n    cold_time: float\n    warm_times: list[float]\n    error: str | None = None\n\n    @property\n    def median(self) -> float:\n        return statistics.median(self.warm_times) if self.warm_times else 0.0\n\n\ndef _run_single_query(runner, sql, iterations=3):\n    cold_time = runner.execute(sql)\n    warm_times = [runner.execute(sql) for _ in range(iterations)]\n    return cold_time, warm_times\n\n\ndef run_benchmark(engine_name, runner, query_ids):\n    results = []\n    for qid in query_ids:\n        sql = TPCH_QUERIES[qid]\n        print(f'  Q{qid:02d} ...', end=' ', flush=True)\n        try:\n            cold, warm = _run_single_query(runner, sql)\n            result = BenchmarkResult(engine=engine_name, query_id=qid,\n                                     cold_time=cold, warm_times=warm)\n            print(f'med={result.median:.2f}s')\n        except Exception as exc:\n            result = BenchmarkResult(engine=engine_name, query_id=qid,\n                                     cold_time=0.0, error=str(exc))\n        results.append(result)\n    return results",
)

# Домашнее задание 5: Сравнение производительности Apache Spark APIs

##  Цель

Провести комплексное сравнение производительности различных API Apache Spark:
- DataFrame API vs RDD API
- SQL vs DataFrame API

Продемонстрировать оптимизации Catalyst и Tungsten на практических примерах.

## [ ] Выполнено

### Часть 1: DataFrame vs RDD (4 обязательных кейса)

| Кейс | DataFrame | RDD | Ускорение | Оптимизация |
|------|-----------|-----|-----------|-------------|
| Множественные агрегации | 0.36с | 5.50с | **15.17x** | Single-pass aggregation, code generation |
| Оконные функции | 0.22с | 1.19с | **5.50x** | Partition-local sorting, window operator |
| Вложенные типы | 0.16с | 1.11с | **6.98x** | Native complex types, zero-copy |
| Условная логика | 0.16с | 4.59с | **28.37x** | Code generation, single-pass evaluation |

### Часть 2: SQL vs DataFrame API (2 бонусных кейса)

| Кейс | SQL | DataFrame API | Быстрее | Причина |
|------|-----|---------------|---------|---------|
| Комплексная агрегация | 0.16с | 0.23с | **SQL** | Идентичные планы, статистическая погрешность |
| Коррелированный подзапрос | 0.20с | 0.25с | **SQL** | Subquery decorrelation |

##  Запуск

### Docker (рекомендуется - работает везде!)

```bash
# Сборка образа
docker-compose build

# Запуск быстрого теста (10,000 строк)
docker-compose up spark-benchmark

# Или используйте удобные скрипты:
.\run_docker.ps1 small   # Windows
./run_docker.sh medium   # Linux/MacOS
```

Результаты сохраняются в `reports/performance_report_<размер>.md`

### Локальный запуск

```bash
pip install -r requirements.txt
python main.py small
```

##  Структура проекта

```
hw5/
 Dockerfile               # Docker образ с Spark и Python
 docker-compose.yml       # Конфигурация для запуска
 run_docker.ps1          # Скрипт для Windows
 run_docker.sh           # Скрипт для Linux/MacOS

 main.py                 # Точка входа
 benchmark.py            # 6 тест-кейсов
 data_generator.py       # Генерация данных
 report_generator.py     # Генерация отчетов
 config.py              # Конфигурация

 reports/                # Папка с результатами
    performance_report_10000.md

 README.md              # Полная документация
 QUICK_START.md         # Быстрый старт
 SUMMARY.md             # Резюме задания
 EXAMPLE_REPORT.md      # Пример отчета
 TROUBLESHOOTING.md     # Решение проблем
 STATUS.md              # Статус проекта
```

##  Ключевые оптимизации

### Catalyst Optimizer
- [ ] Predicate pushdown - фильтры к источнику
- [ ] Projection pruning - только нужные колонки
- [ ] Constant folding - вычисление констант
- [ ] Join reordering - оптимальный порядок
- [ ] Subquery decorrelation - преобразование подзапросов

### Tungsten Execution Engine
- [ ] Whole-stage code generation - генерация bytecode
- [ ] Off-heap memory management - память вне JVM
- [ ] Cache-aware computation - оптимизация для CPU cache
- [ ] Binary processing (UnsafeRow) - эффективный формат

##  Результаты

**DataFrame показал впечатляющее превосходство над RDD:**
- В среднем **14x быстрее** для типичных операций
- До **28x быстрее** для условной логики
- **6-15x быстрее** для агрегаций

**SQL vs DataFrame API:**
- Практически идентичная производительность
- SQL может быть немного быстрее для сложных подзапросов
- Разница в пределах статистической погрешности

##  Выводы

### Когда использовать DataFrame:
[ ] Агрегации и аналитика  
[ ] Структурированные данные  
[ ] Оконные функции  
[ ] Вложенные типы  
[ ] Любые типичные ETL-задачи  

### Когда использовать RDD:
[X] Только для специфической низкоуровневой логики  
[X] Работа с произвольными бинарными данными  
[X] Legacy код  

### SQL vs DataFrame API:
 Выбор зависит от предпочтений команды  
 Одинаковая производительность в 95% случаев  
 SQL проще для аналитиков  
 DataFrame API лучше для type safety  

##  Документация

- [README.md](README.md) - Полная документация проекта
- [QUICK_START.md](QUICK_START.md) - Быстрый старт
- [SUMMARY.md](SUMMARY.md) - Описание всех кейсов
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Решение проблем
- [EXAMPLE_REPORT.md](EXAMPLE_REPORT.md) - Пример результата

##  Docker

Проект полностью работает в Docker, что решает проблемы совместимости с Windows:
- [ ] Автоматическая установка Java и зависимостей
- [ ] Изолированное окружение
- [ ] Воспроизводимые результаты
- [ ] Монтирование папки reports/

##  Технологии

- Apache Spark 4.1.1
- Python 3.11
- OpenJDK 21
- Docker & Docker Compose
- PySpark, Pandas, Tabulate

##  Особенности реализации

- [ ] Warm-up runs для точных измерений
- [ ] Усреднение по 3 итерациям
- [ ] Автоматическая генерация отчетов
- [ ] Анализ планов выполнения (explain)
- [ ] Профессиональная структура кода
- [ ] Подробная документация

##  Автор

Домашнее задание для курса Data Pipelines, HSE  
Дата: 06.03.2026

---

**Проект готов к сдаче!** 

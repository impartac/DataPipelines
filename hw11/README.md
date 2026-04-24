# Универсальные WorkflowTemplate для Argo Workflows

Этот проект содержит набор универсальных и переиспользуемых WorkflowTemplate для Argo Workflows, которые решают частые задачи оркестрации данных.

## 📋 Содержание

- [Обзор шаблонов](#обзор-шаблонов)
- [Структура проекта](#структура-проекта)
- [Установка и настройка](#установка-и-настройка)
- [Детальное описание шаблонов](#детальное-описание-шаблонов)
- [Использование](#использование)
- [Примеры](#примеры)

## 🎯 Обзор шаблонов

Проект включает 5 универсальных шаблонов:

| Шаблон | Назначение | Ключевые возможности |
|--------|-----------|---------------------|
| **Data Validation** | Проверка корректности данных | Валидация схемы, проверка NULL, дубликатов |
| **ETL Processing** | Обработка данных | Extract-Transform-Load с различными трансформациями |
| **Notification Sender** | Отправка уведомлений | Slack, Email, Teams, Webhook |
| **Conditional Execution** | Условная логика | Пороговые значения, статусы, regex |
| **Batch File Processor** | Пакетная обработка | Анализ, копирование, сжатие файлов |

## 📁 Структура проекта

```
hw11/
├── workflow-templates.yaml    # Все 5 универсальных шаблонов
├── main-workflow.yaml         # Основной пайплайн, использующий все шаблоны
├── examples.yaml              # Примеры использования каждого шаблона
├── setup.ps1                  # 🚀 Автоматическая установка (1 команда!)
├── docker-compose.yml         # Docker Compose для вспомогательных сервисов
├── DOCKER_SETUP.md            # 📖 Подробное руководство по Docker (для защиты)
├── README.md                  # Эта документация
├── QUICKSTART.md              # Быстрый старт
├── DEPLOYMENT.md              # Руководство по развертыванию
├── ARCHITECTURE.md            # Архитектурные диаграммы
├── REFERENCE.md               # Справочник параметров
└── SUMMARY.md                 # Резюме проекта
```

## 🚀 Установка и настройка

### ⚡ Быстрый старт (Docker) - РЕКОМЕНДУЕТСЯ

**Запуск всего окружения одной командой!**

#### Требования
- Windows 10/11
- Docker Desktop установлен и запущен

#### Установка (5-10 минут)

```powershell
# 1. Перейдите в папку hw11
cd hw11

# 2. Запустите автоматическую установку
.\setup.ps1

# Готово! 🎉
# Argo UI: http://localhost:2746
```

**Что устанавливается автоматически:**
- ✅ k3d (Kubernetes in Docker)
- ✅ kubectl (CLI для Kubernetes)
- ✅ Argo Workflows + UI
- ✅ Все 5 WorkflowTemplates
- ✅ Вспомогательные сервисы (MinIO, PostgreSQL, MailHog)

**Дополнительные опции:**

```powershell
# Запуск с примерами
.\setup.ps1 -RunExamples

# Полная переустановка
.\setup.ps1 -CleanStart

# Быстрый перезапуск (если зависимости уже установлены)
.\setup.ps1 -SkipInstall
```

**Полная документация по Docker установке:**
- 📖 **[DOCKER_SETUP.md](DOCKER_SETUP.md)** - Подробное руководство с объяснением архитектуры (для защиты проекта)

**Остановка и удаление:**

```powershell
# Остановить кластер (данные сохраняются)
k3d cluster stop argo-workflows

# Запустить снова
k3d cluster start argo-workflows

# Полностью удалить
k3d cluster delete argo-workflows
docker-compose down -v
```

---

### 🔧 Ручная установка (без Docker)

Если вы хотите установить на существующий Kubernetes кластер:

#### Предварительные требования

1. Kubernetes кластер (версия 1.20+)
2. Установленный Argo Workflows (версия 3.0+)
3. kubectl настроенный для работы с кластером

### Развертывание шаблонов

```bash
# 1. Создать namespace для Argo (если еще не создан)
kubectl create namespace argo

# 2. Применить все WorkflowTemplate
kubectl apply -f workflow-templates.yaml

# 3. Проверить установку
kubectl get workflowtemplates -n argo

# Ожидаемый вывод:
# NAME                               AGE
# data-validation-template           5s
# etl-processing-template           5s
# notification-template             5s
# conditional-execution-template    5s
# batch-file-processor-template     5s
```

### Запуск основного пайплайна

```bash
# Запуск с параметрами по умолчанию
kubectl create -f main-workflow.yaml

# Запуск с кастомными параметрами
argo submit main-workflow.yaml \
  -p input-data-path="s3://my-bucket/data.csv" \
  -p processing-mode="thorough" \
  -p notification-recipients="team@company.com"

# Просмотр статуса
argo list

# Просмотр логов
argo logs @latest
```

## 📖 Детальное описание шаблонов

### 1. Data Validation Template

**Файл:** `data-validation-template`

**Назначение:** Проверка корректности и качества данных перед обработкой.

#### Входные параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `data-path` | string | - | Путь к файлу данных (S3, local, URL) |
| `validation-rules` | JSON | `{"check_schema": true, ...}` | Правила валидации |
| `fail-on-error` | boolean | `false` | Завершать ли workflow при ошибке |
| `data-format` | string | `csv` | Формат данных: csv, json, parquet, avro |

#### Выходные параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `validation-status` | string | success/failed |
| `error-count` | integer | Количество ошибок |
| `validation-report` | JSON | Подробный отчет о валидации |

#### Пример использования

```yaml
- name: validate-data
  templateRef:
    name: data-validation-template
    template: validate
  arguments:
    parameters:
    - name: data-path
      value: "s3://bucket/data.csv"
    - name: validation-rules
      value: |
        {
          "check_schema": true,
          "check_nulls": true,
          "check_duplicates": true,
          "min_records": 1000,
          "required_columns": ["id", "name", "email"]
        }
    - name: fail-on-error
      value: "true"
```

#### Validation Rules - Поддерживаемые правила

```json
{
  "check_schema": true,              // Проверка схемы данных
  "check_nulls": true,                // Проверка NULL значений
  "check_duplicates": true,           // Проверка дубликатов
  "min_records": 100,                 // Минимальное количество записей
  "max_records": 1000000,             // Максимальное количество записей
  "required_columns": ["col1", "col2"], // Обязательные колонки
  "column_types": {                   // Ожидаемые типы колонок
    "age": "integer",
    "email": "string"
  }
}
```

---

### 2. ETL Processing Template

**Файл:** `etl-processing-template`

**Назначение:** Extract-Transform-Load обработка данных с различными типами трансформаций.

#### Входные параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `source-path` | string | - | Путь к исходным данным |
| `target-path` | string | - | Путь для сохранения результата |
| `transformation-type` | string | `filter` | filter, aggregate, join, enrich |
| `transformation-config` | JSON | `{}` | Конфигурация трансформации |
| `chunk-size` | integer | `1000` | Размер чанка для обработки |
| `source-format` | string | `csv` | Формат исходных данных |
| `target-format` | string | `parquet` | Формат результата |

#### Выходные параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `records-processed` | integer | Количество обработанных записей |
| `processing-time` | float | Время обработки в секундах |
| `output-size` | integer | Размер выходного файла в байтах |

#### Выходные артефакты

| Артефакт | Путь | Описание |
|----------|------|----------|
| `processed-data` | `/tmp/output` | Обработанные данные |

#### Типы трансформаций

**Filter** - Фильтрация данных
```json
{
  "filter_column": "status",
  "filter_value": "completed",
  "filter_operator": "eq"
}
```

**Aggregate** - Агрегация данных
```json
{
  "group_by": ["customer_id", "date"],
  "aggregations": {
    "amount": "sum",
    "order_id": "count"
  }
}
```

**Join** - Соединение данных
```json
{
  "join_type": "left",
  "join_table": "s3://bucket/reference.parquet",
  "join_on": "customer_id"
}
```

**Enrich** - Обогащение данных
```json
{
  "lookup_table": "s3://bucket/enrichment.csv",
  "lookup_key": "id",
  "enrich_columns": ["category", "region"]
}
```

---

### 3. Notification Template

**Файл:** `notification-template`

**Назначение:** Отправка уведомлений о статусе выполнения workflow.

#### Входные параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `notification-type` | string | `slack` | email, slack, webhook, teams |
| `recipients` | string | - | Получатели (через запятую) |
| `subject` | string | - | Тема сообщения |
| `message` | string | - | Текст сообщения |
| `status` | string | `info` | success, warning, error, info |
| `webhook-url` | string | `""` | URL webhook для Slack/Teams |
| `include-metadata` | boolean | `true` | Включать метаданные workflow |

#### Выходные параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `notification-sent` | boolean | Успешность отправки |
| `send-timestamp` | string | Время отправки (ISO 8601) |

#### Примеры для разных типов

**Slack:**
```yaml
- name: notify-slack
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
```

**Email:**
```yaml
- name: notify-email
  templateRef:
    name: notification-template
    template: send
  arguments:
    parameters:
    - name: notification-type
      value: "email"
    - name: recipients
      value: "manager@company.com,team@company.com"
    - name: subject
      value: "Daily Report"
    - name: message
      value: "The daily report is ready"
    - name: status
      value: "info"
```

---

### 4. Conditional Execution Template

**Файл:** `conditional-execution-template`

**Назначение:** Условное выполнение шагов на основе различных критериев.

#### Входные параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `condition-type` | string | `threshold` | threshold, status, regex, range |
| `condition-value` | string | - | Значение для проверки |
| `condition-operator` | string | `gt` | gt, lt, eq, ne, gte, lte, contains, matches |
| `threshold` | string | `0` | Пороговое значение |
| `default-decision` | string | `skip` | Решение по умолчанию |

#### Выходные параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `condition-result` | boolean | Результат проверки (true/false) |
| `execution-decision` | string | execute/skip |
| `decision-reason` | string | Причина решения |

#### Операторы сравнения

| Оператор | Описание | Пример |
|----------|----------|--------|
| `gt` | Больше | `100 > 50` |
| `lt` | Меньше | `50 < 100` |
| `gte` | Больше или равно | `100 >= 100` |
| `lte` | Меньше или равно | `50 <= 100` |
| `eq` | Равно | `"success" == "success"` |
| `ne` | Не равно | `"failed" != "success"` |
| `contains` | Содержит | `"completed" in "status:completed"` |
| `matches` | Regex совпадение | `"test123" matches /test\d+/` |

#### Примеры условий

**Проверка порогового значения:**
```yaml
- name: check-record-count
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

**Проверка статуса:**
```yaml
- name: check-validation-status
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

---

### 5. Batch File Processor Template

**Файл:** `batch-file-processor-template`

**Назначение:** Пакетная обработка множества файлов с различными операциями.

#### Входные параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `source-directory` | string | - | Директория с файлами |
| `file-pattern` | string | `*.*` | Паттерн фильтрации (*.csv, *.json) |
| `operation` | string | `analyze` | copy, move, transform, analyze, compress |
| `target-directory` | string | `/tmp/target` | Целевая директория |
| `parallel-workers` | integer | `4` | Количество параллельных воркеров |
| `fail-fast` | boolean | `false` | Остановка при первой ошибке |

#### Выходные параметры

| Параметр | Тип | Описание |
|----------|-----|----------|
| `files-processed` | integer | Количество обработанных файлов |
| `files-failed` | integer | Количество файлов с ошибками |
| `total-size` | integer | Общий размер обработанных файлов (байты) |
| `file-list` | JSON | Список обработанных файлов с деталями |

#### Поддерживаемые операции

| Операция | Описание | Использование |
|----------|----------|---------------|
| `analyze` | Анализ файлов (размер, формат) | Аудит данных |
| `copy` | Копирование файлов | Резервное копирование |
| `move` | Перемещение файлов | Архивирование |
| `transform` | Трансформация файлов | Конвертация форматов |
| `compress` | Сжатие файлов | Оптимизация хранения |

#### Пример использования

```yaml
- name: compress-all-csv
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
    - name: parallel-workers
      value: "10"
    - name: fail-fast
      value: "false"
```

---

## 🔧 Использование

### Основной пайплайн

Файл `main-workflow.yaml` демонстрирует использование всех шаблонов в едином пайплайне обработки данных:

```
Старт → Уведомление
  ↓
Валидация данных
  ↓
Проверка результата валидации
  ↓
ETL обработка (если валидация успешна)
  ↓
Проверка качества (порог количества записей)
  ↓
Пакетная обработка (если QA прошла)
  ↓
Финальное уведомление (успех/ошибка)
```

### Параметры основного workflow

```yaml
# Запуск с кастомными параметрами
argo submit main-workflow.yaml \
  -p input-data-path="s3://my-bucket/data.csv" \
  -p output-data-path="s3://my-bucket/processed/" \
  -p processing-mode="thorough" \
  -p notification-recipients="team@company.com" \
  -p quality-threshold="5000" \
  -p batch-file-pattern="*.parquet"
```

### Использование отдельных шаблонов

Каждый шаблон можно использовать независимо в любом workflow через `templateRef`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: my-workflow-
spec:
  entrypoint: main
  templates:
  - name: main
    steps:
    - - name: my-step
        templateRef:
          name: data-validation-template  # Имя шаблона
          template: validate              # Имя template внутри WorkflowTemplate
        arguments:
          parameters:
          - name: data-path
            value: "s3://bucket/data.csv"
```

---

## 📚 Примеры

Файл `examples.yaml` содержит полные рабочие примеры для каждого шаблона:

### Пример 1: Валидация данных
```bash
kubectl create -f examples.yaml --selector=example=validation
```

### Пример 2: ETL обработка с параллельными трансформациями
```bash
kubectl create -f examples.yaml --selector=example=etl
```

### Пример 3: Мультиканальные уведомления
```bash
kubectl create -f examples.yaml --selector=example=notification
```

### Пример 4: Условное выполнение
```bash
kubectl create -f examples.yaml --selector=example=conditional
```

### Пример 5: Пакетная обработка
```bash
kubectl create -f examples.yaml --selector=example=batch
```

### Пример 6: Обработка ошибок
```bash
kubectl create -f examples.yaml --selector=example=error-handling
```

---

## 🎨 Расширение шаблонов

### Добавление новых типов трансформаций

Чтобы добавить новый тип трансформации в ETL шаблон:

1. Отредактируйте `workflow-templates.yaml`
2. Добавьте новый case в блок трансформации:

```python
elif transformation_type == "custom":
    # Ваша кастомная трансформация
    records_processed = custom_transformation(records_read)
```

### Добавление новых типов уведомлений

Для добавления нового канала уведомлений:

```python
elif notification_type == "telegram":
    print(f"Sending to Telegram...")
    telegram_payload = {
        "chat_id": recipients,
        "text": full_message
    }
    # requests.post(telegram_api_url, json=telegram_payload)
```

---

## 🔐 Безопасность

### Секреты для уведомлений

Используйте Kubernetes Secrets для хранения webhook URLs и credentials:

```yaml
# Создание secret
kubectl create secret generic notifications \
  --from-literal=slack-webhook-url=https://hooks.slack.com/... \
  --from-literal=email-password=xxx \
  -n argo

# Использование в workflow
- name: webhook-url
  valueFrom:
    secretKeyRef:
      name: notifications
      key: slack-webhook-url
```

### Доступ к S3

Для доступа к S3 bucket настройте IRSA (IAM Roles for Service Accounts):

```yaml
serviceAccountName: argo-workflow-sa
```

---

## 📊 Мониторинг и логирование

### Просмотр логов

```bash
# Все логи workflow
argo logs <workflow-name>

# Логи конкретного шага
argo logs <workflow-name> <step-name>

# Следить за логами в реальном времени
argo logs -f <workflow-name>
```

### Метрики

Все шаблоны выводят метрики в outputs:
- Время выполнения
- Количество обработанных записей
- Размер данных
- Количество ошибок

Эти метрики можно собирать и визуализировать в Grafana.

---

## 🐛 Отладка

### Проверка статуса workflow

```bash
# Список всех workflows
argo list

# Детали конкретного workflow
argo get <workflow-name>

# Посмотреть состояние шагов
kubectl describe workflow <workflow-name> -n argo
```

### Типичные проблемы

**Проблема:** Workflow не запускается
```bash
# Проверить события
kubectl get events -n argo --sort-by='.lastTimestamp'

# Проверить наличие шаблонов
kubectl get workflowtemplates -n argo
```

**Проблема:** Шаблон не найден
```bash
# Убедиться, что шаблон в правильном namespace
kubectl get workflowtemplates -n argo

# Проверить имя шаблона в templateRef
```

---

## 📈 Best Practices

1. **Параметризация**: Всегда используйте параметры вместо hardcoded значений
2. **Обработка ошибок**: Используйте `continueOn` и `onExit` для обработки ошибок
3. **Уведомления**: Настройте уведомления для важных событий
4. **Условное выполнение**: Используйте conditional template для гибкости
5. **Ресурсы**: Настройте limits и requests для container'ов
6. **Таймауты**: Устанавливайте разумные activeDeadlineSeconds
7. **Логирование**: Добавляйте подробные print statements для отладки
8. **Версионирование**: Используйте семантическое версионирование для шаблонов

---

## 📝 Лицензия и вклад

Этот проект создан в образовательных целях для курса Data Pipelines HSE.

**Автор**: Студент HSE  
**Дата**: Апрель 2026

---

## 🔗 Дополнительные ресурсы

- [Argo Workflows Documentation](https://argoproj.github.io/argo-workflows/)
- [WorkflowTemplates Guide](https://argoproj.github.io/argo-workflows/workflow-templates/)
- [Argo Examples](https://github.com/argoproj/argo-workflows/tree/master/examples)
- [Best Practices](https://argoproj.github.io/argo-workflows/best-practices/)

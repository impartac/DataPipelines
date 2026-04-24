# ⚡ Быстрый старт - Argo Workflow Templates

## 🎯 Что это?

Набор из **5 универсальных WorkflowTemplate** для Argo Workflows, которые решают частые задачи оркестрации данных.

## 📦 Файлы проекта

| Файл | Описание |
|------|----------|
| `workflow-templates.yaml` | 5 универсальных шаблонов (основной файл) |
| `main-workflow.yaml` | Полный data pipeline, использующий все шаблоны |
| `examples.yaml` | 6 примеров использования каждого шаблона |
| `README.md` | Полная документация |
| `DEPLOYMENT.md` | Детальное руководство по развертыванию |
| `ARCHITECTURE.md` | Архитектурные диаграммы |
| `QUICKSTART.md` | Этот файл - быстрый старт |

---

## 🚀 Быстрая установка (5 минут)

### Шаг 1: Установка Argo Workflows

```bash
# Создать namespace
kubectl create namespace argo

# Установить Argo Workflows
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.5.0/install.yaml

# Проверить установку
kubectl get pods -n argo
```

### Шаг 2: Установка шаблонов

```bash
# Применить все шаблоны
kubectl apply -f workflow-templates.yaml -n argo

# Проверить
kubectl get workflowtemplates -n argo
```

### Шаг 3: Запуск примера

```bash
# Запустить основной пайплайн
kubectl create -f main-workflow.yaml -n argo

# Или через Argo CLI
argo submit main-workflow.yaml -n argo --watch
```

### Шаг 4: Просмотр результатов

```bash
# UI (в браузере откроется localhost:2746)
kubectl -n argo port-forward deployment/argo-server 2746:2746

# CLI
argo list -n argo
argo get <workflow-name> -n argo
argo logs <workflow-name> -n argo
```

---

## 📋 Список шаблонов

### 1️⃣ Data Validation Template
**Что делает:** Проверяет корректность данных перед обработкой  
**Входы:** путь к данным, правила валидации  
**Выходы:** статус (success/failed), количество ошибок, отчет  

```yaml
- name: validate
  templateRef:
    name: data-validation-template
    template: validate
  arguments:
    parameters:
    - name: data-path
      value: "s3://bucket/data.csv"
    - name: validation-rules
      value: '{"check_schema": true, "check_nulls": true}'
```

---

### 2️⃣ ETL Processing Template
**Что делает:** Extract-Transform-Load обработка данных  
**Входы:** source path, target path, тип трансформации  
**Выходы:** количество записей, время обработки, размер  

```yaml
- name: process
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
```

**Типы трансформаций:**
- `filter` - фильтрация данных
- `aggregate` - агрегация
- `join` - соединение таблиц
- `enrich` - обогащение данных

---

### 3️⃣ Notification Template
**Что делает:** Отправляет уведомления о статусе workflow  
**Входы:** тип (slack/email/teams), получатели, сообщение  
**Выходы:** статус отправки, timestamp  

```yaml
- name: notify
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
      value: "Processing finished successfully"
    - name: status
      value: "success"
```

**Поддерживаемые каналы:**
- Slack (webhook)
- Email (SMTP)
- Microsoft Teams
- Generic Webhook

---

### 4️⃣ Conditional Execution Template
**Что делает:** Условное выполнение шагов  
**Входы:** тип условия, значение, оператор, порог  
**Выходы:** результат (true/false), решение (execute/skip)  

```yaml
- name: check
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

**Типы условий:**
- `threshold` - числовое сравнение (>, <, >=, <=, ==, !=)
- `status` - проверка статуса (eq, ne, contains)
- `regex` - регулярное выражение
- `range` - проверка диапазона

---

### 5️⃣ Batch File Processor Template
**Что делает:** Пакетная обработка множества файлов  
**Входы:** директория, паттерн файлов, операция  
**Выходы:** количество обработанных файлов, размер, список  

```yaml
- name: batch
  templateRef:
    name: batch-file-processor-template
    template: process-batch
  arguments:
    parameters:
    - name: source-directory
      value: "s3://bucket/files/"
    - name: file-pattern
      value: "*.csv"
    - name: operation
      value: "compress"
    - name: parallel-workers
      value: "10"
```

**Операции:**
- `analyze` - анализ файлов
- `copy` - копирование
- `move` - перемещение
- `compress` - сжатие
- `transform` - трансформация

---

## 🔗 Основной пайплайн

Файл `main-workflow.yaml` объединяет все шаблоны:

```
1. Старт → Notification
2. Data Validation
3. Check Status (Conditional)
4. ETL Processing (if valid)
5. Quality Check (Conditional)
6. Batch Processing (if QA passed)
7. Final Notification (success/failure)
```

### Параметры основного пайплайна

```bash
argo submit main-workflow.yaml \
  -p input-data-path="s3://my-bucket/data.csv" \
  -p output-data-path="s3://my-bucket/processed/" \
  -p processing-mode="standard" \
  -p notification-recipients="team@company.com" \
  -p quality-threshold="1000" \
  -p batch-file-pattern="*.parquet"
```

---

## 📚 Примеры использования

### Пример 1: Простая валидация

```bash
# Запуск только валидации
kubectl create -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: validate-example-
  namespace: argo
spec:
  entrypoint: main
  templates:
  - name: main
    steps:
    - - name: validate
        templateRef:
          name: data-validation-template
          template: validate
        arguments:
          parameters:
          - name: data-path
            value: "s3://my-bucket/data.csv"
          - name: validation-rules
            value: '{"check_schema": true, "check_nulls": true}'
EOF
```

### Пример 2: ETL + Notification

```bash
# Запуск ETL с уведомлением
kubectl create -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: etl-example-
  namespace: argo
spec:
  entrypoint: main
  templates:
  - name: main
    steps:
    - - name: process
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
    
    - - name: notify
        templateRef:
          name: notification-template
          template: send
        arguments:
          parameters:
          - name: notification-type
            value: "slack"
          - name: recipients
            value: "#team"
          - name: subject
            value: "ETL Completed"
          - name: message
            value: "Processed {{steps.process.outputs.parameters.records-processed}} records"
          - name: status
            value: "success"
EOF
```

### Пример 3: Условное выполнение

```bash
# Запуск с условием
kubectl create -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: conditional-example-
  namespace: argo
spec:
  entrypoint: main
  templates:
  - name: main
    steps:
    - - name: validate
        templateRef:
          name: data-validation-template
          template: validate
        arguments:
          parameters:
          - name: data-path
            value: "s3://bucket/data.csv"
    
    - - name: check
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
    
    - - name: process-if-valid
        templateRef:
          name: etl-processing-template
          template: process
        when: "{{steps.check.outputs.parameters.execution-decision}} == execute"
        arguments:
          parameters:
          - name: source-path
            value: "s3://bucket/data.csv"
          - name: target-path
            value: "s3://bucket/output/"
EOF
```

---

## 🛠️ Полезные команды

### Управление workflows

```bash
# Список всех workflows
argo list -n argo

# Детали workflow
argo get <workflow-name> -n argo

# Логи workflow
argo logs <workflow-name> -n argo

# Логи в реальном времени
argo logs -f <workflow-name> -n argo

# Остановить workflow
argo stop <workflow-name> -n argo

# Удалить workflow
argo delete <workflow-name> -n argo

# Повторить workflow
argo retry <workflow-name> -n argo
```

### Управление шаблонами

```bash
# Список шаблонов
kubectl get workflowtemplates -n argo

# Детали шаблона
kubectl describe workflowtemplate data-validation-template -n argo

# YAML шаблона
kubectl get workflowtemplate data-validation-template -n argo -o yaml

# Удалить шаблон
kubectl delete workflowtemplate data-validation-template -n argo
```

### Отладка

```bash
# События в namespace
kubectl get events -n argo --sort-by='.lastTimestamp'

# Логи workflow controller
kubectl logs -n argo deployment/workflow-controller

# Статус pod'ов
kubectl get pods -n argo

# Детали pod'а
kubectl describe pod <pod-name> -n argo
```

---

## 🎓 Обучающие материалы

### Документация
- [README.md](README.md) - Полная документация всех шаблонов
- [DEPLOYMENT.md](DEPLOYMENT.md) - Детальное руководство по развертыванию
- [ARCHITECTURE.md](ARCHITECTURE.md) - Архитектурные диаграммы

### Примеры
- [examples.yaml](examples.yaml) - 6 рабочих примеров

### Официальные ресурсы
- [Argo Workflows Docs](https://argoproj.github.io/argo-workflows/)
- [WorkflowTemplates Guide](https://argoproj.github.io/argo-workflows/workflow-templates/)
- [GitHub Examples](https://github.com/argoproj/argo-workflows/tree/master/examples)

---

## 🎯 Следующие шаги

1. **Изучите шаблоны** - откройте `workflow-templates.yaml` и посмотрите код
2. **Запустите примеры** - попробуйте каждый пример из `examples.yaml`
3. **Модифицируйте** - измените параметры под свои нужды
4. **Создайте свой workflow** - используйте шаблоны как building blocks
5. **Настройте production** - следуйте `DEPLOYMENT.md` для production setup

---

## 💡 Best Practices

### ✅ DO:
- Используйте параметры для гибкости
- Добавляйте уведомления для важных событий
- Используйте conditional execution для сложной логики
- Настройте retry политики
- Добавьте таймауты
- Логируйте промежуточные результаты

### ❌ DON'T:
- Не hardcode значения в шаблонах
- Не игнорируйте ошибки
- Не забывайте про resource limits
- Не запускайте без валидации
- Не пропускайте уведомления об ошибках

---

## 🤔 FAQ

**Q: Как передать результат из одного шага в другой?**
```yaml
# Шаг 1 - генерирует output
- name: step1
  outputs:
    parameters:
    - name: result
      value: "some-value"

# Шаг 2 - использует output из шага 1
- name: step2
  inputs:
    parameters:
    - name: input-value
      value: "{{steps.step1.outputs.parameters.result}}"
```

**Q: Как сделать параллельное выполнение?**
```yaml
# Параллельные шаги - используйте двойной дефис
steps:
- - name: parallel-step-1
    template: task1
  - name: parallel-step-2
    template: task2
  - name: parallel-step-3
    template: task3
```

**Q: Как добавить условие выполнения?**
```yaml
- name: conditional-step
  template: my-template
  when: "{{steps.check.outputs.parameters.result}} == true"
```

**Q: Как настроить retry при ошибках?**
```yaml
retryStrategy:
  limit: 3
  retryPolicy: "OnFailure"
  backoff:
    duration: "30s"
    factor: 2
```

---

## 📞 Помощь

Если что-то не работает:
1. Проверьте логи: `argo logs <workflow-name> -n argo`
2. Проверьте события: `kubectl get events -n argo`
3. Проверьте шаблоны: `kubectl get workflowtemplates -n argo`
4. Изучите документацию в `README.md`
5. Посмотрите примеры в `examples.yaml`

---

## ✨ Краткая справка по шаблонам

```bash
# 1. Data Validation
templateRef: data-validation-template / validate
inputs: data-path, validation-rules, fail-on-error, data-format
outputs: validation-status, error-count, validation-report

# 2. ETL Processing
templateRef: etl-processing-template / process
inputs: source-path, target-path, transformation-type, transformation-config
outputs: records-processed, processing-time, output-size

# 3. Notification
templateRef: notification-template / send
inputs: notification-type, recipients, subject, message, status
outputs: notification-sent, send-timestamp

# 4. Conditional Execution
templateRef: conditional-execution-template / evaluate
inputs: condition-type, condition-value, condition-operator, threshold
outputs: condition-result, execution-decision, decision-reason

# 5. Batch File Processor
templateRef: batch-file-processor-template / process-batch
inputs: source-directory, file-pattern, operation, parallel-workers
outputs: files-processed, files-failed, total-size, file-list
```

---

**Готово! Теперь вы можете начать использовать универсальные WorkflowTemplate для Argo Workflows! 🚀**

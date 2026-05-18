# hw12 — CI/CD Pipeline для Kubernetes

Полный CI/CD пайплайн для развёртывания разнородных приложений в Kubernetes:
Spark-приложения, сторонних продуктов из Helm и самописных витрин данных.

## Быстрый старт (локальная демонстрация)

```powershell
git checkout feature/cicd-pipeline
cd hw12
.\build-local.ps1
```

Результат: два Docker-образа собраны и опубликованы в локальный реестр,
ETL-джоба обработала 10 000 записей, Dashboard доступен на http://localhost:8080.

## Структура репозитория

```
hw12/
├── .gitlab-ci.yml                    # CI/CD пайплайн (6 стадий)
├── docker-compose.yml                # Локальная среда разработки
├── build-local.ps1                   # Скрипт локальной демонстрации
│
├── apps/
│   ├── spark-jobs/data-processor/    # Spark ETL приложение
│   │   ├── src/main.py               # ETL логика (10k записей → агрегация)
│   │   ├── Dockerfile                # Multi-stage build (python:3.10-slim)
│   │   └── requirements.txt
│   │
│   └── dashboards/data-ui/           # Витрина данных
│       ├── public/index.html         # Dashboard (HTML + CSS + JS)
│       ├── nginx.conf                # nginx config + /health endpoint
│       └── Dockerfile                # Multi-stage (node:20-alpine → nginx)
│
├── helm/
│   ├── third-party/                  # Helm values для внешних чартов
│   │   ├── argo-workflows/values.yaml
│   │   ├── minio/values.yaml
│   │   ├── spark-operator/values.yaml
│   │   └── postgresql/values.yaml
│   └── internal/data-ui/             # Helm чарт для витрины
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│
├── kustomize/                        # Kustomize оверлеи
│   ├── base/                         # Базовая конфигурация
│   └── overlays/
│       ├── dev/                      # 1 реплика, :dev тег
│       ├── staging/                  # 2 реплики
│       └── prod/                     # 3 реплики, повышенные лимиты
│
└── argo-workflows/
    ├── templates/
    │   └── universal-templates.yaml  # 5 WorkflowTemplate (из hw11)
    └── jobs/
        ├── spark-data-processing.yaml # Workflow для Spark ETL
        └── generate-workflow.ps1      # Генератор workflow с тегом образа
```

## CI/CD Пайплайн (.gitlab-ci.yml)

### Стадии

| Стадия    | Джобы                              | Описание                              |
|-----------|------------------------------------|---------------------------------------|
| `lint`    | python-lint, yaml-lint, dockerfile-lint | Статический анализ кода          |
| `build`   | build-spark, build-ui              | Docker BuildKit с layer caching       |
| `publish` | publish-spark, publish-ui          | Push в GitLab Container Registry      |
| `deploy`  | deploy-third-party, deploy-internal | Helm + Kustomize в Kubernetes         |
| `workflow`| trigger-spark-workflow             | Argo Workflow с текущим тегом образа  |
| `notify`  | notify-success, notify-failure     | Slack уведомления                     |

### Переменные CI

| Переменная         | Значение                        |
|--------------------|---------------------------------|
| `KUBE_NAMESPACE`   | `data-pipelines`                |
| `REGISTRY`         | `$CI_REGISTRY`                  |
| `SPARK_IMAGE`      | `$REGISTRY/spark-data-processor`|
| `UI_IMAGE`         | `$REGISTRY/data-ui`             |
| `IMAGE_TAG`        | `$CI_COMMIT_SHORT_SHA`          |

## Технологический стек

### Оркестрация контейнеров
- **Kubernetes (k3d)** — локальный кластер, в продакшне любой managed K8s
- **Helm** — управление третьесторонними продуктами (argo-workflows, minio, spark-operator, postgresql)
- **Kustomize** — конфигурационные оверлеи для dev/staging/prod без дублирования

### Spark-приложение
- **python:3.10-slim** — минимальный образ для ETL джобы
- **Multi-stage Dockerfile** — builder устанавливает зависимости, runtime копирует только нужное
- **Non-root user** `spark` (UID 1000) — соответствует принципу least privilege

### Витрина данных
- **nginx:1.25-alpine** — минимальный веб-сервер (48 MB образ)
- **node:20-alpine** — только для сборки статики (не попадает в финальный образ)
- **Endpoint /health** — для liveness/readiness probe в Kubernetes

### Хранилище артефактов
- **MinIO** — S3-совместимое хранилище для артефактов Argo Workflows
- Buckets: `argo-artifacts` (workflow logs), `spark-output` (ETL результаты)

### CI/CD
- **GitLab CI** — pipeline engine с 6 стадиями
- **GitLab Container Registry** — хранение Docker образов
- **Argo Workflows** — оркестрация Spark джоб через универсальные templates

## Развёртывание third-party через Helm

```bash
# Argo Workflows
helm upgrade --install argo-workflows argo/argo-workflows \
  -n argo --create-namespace \
  -f helm/third-party/argo-workflows/values.yaml

# MinIO
helm upgrade --install minio bitnami/minio \
  -n minio --create-namespace \
  -f helm/third-party/minio/values.yaml

# Spark Operator
helm upgrade --install spark-operator kubeflow/spark-operator \
  -n spark-operator --create-namespace \
  -f helm/third-party/spark-operator/values.yaml
```

## Развёртывание витрины через Kustomize

```bash
# Dev
kubectl apply -k kustomize/overlays/dev

# Production
kubectl apply -k kustomize/overlays/prod
```

## Запуск Spark Workflow в Argo

```powershell
# Применить универсальные templates (из hw11)
kubectl apply -f argo-workflows/templates/ -n argo

# Сгенерировать workflow с текущим тегом
.\argo-workflows\jobs\generate-workflow.ps1 -Tag "abc1234"

# Создать workflow
kubectl create -f argo-workflows/jobs/spark-data-processing-abc1234.yaml -n argo

# Следить за прогрессом
kubectl get workflows -n argo -w
```

## Доказательство работы (локальные логи)

ETL джоба успешно выполнена локально через Docker:

```
============================================================
  SPARK DATA PROCESSING JOB
============================================================
  Job:    demo-etl-job
  Mode:   Local (Python)
  Input:  /data/input
  Output: /data/output
============================================================

[1/4] EXTRACT: Loading source data...
  Generated 10000 synthetic records

[2/4] TRANSFORM: Filtering and aggregating...
  Filtered to 5909 completed orders

[3/4] VALIDATE: Running quality checks...
  Quality check PASSED: 5 categories, all non-empty

[4/4] LOAD: Writing output...
  Written to: /data/output/results.json

============================================================
  JOB COMPLETED SUCCESSFULLY
============================================================
  Input records:   10000
  Processed:       5909
  Output records:  5
============================================================
```

Dashboard доступен по `http://localhost:8080` (контейнер `pipeline-data-ui`).

Образы опубликованы в локальный реестр `localhost:5000`:
- `localhost:5000/spark-data-processor:latest`
- `localhost:5000/data-ui:latest`

## Ветка

Вся работа выполнена в ветке `feature/cicd-pipeline`.

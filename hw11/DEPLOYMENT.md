# Руководство по развертыванию Argo Workflows Templates

## 📦 Полное руководство по установке и настройке

### Шаг 1: Установка Argo Workflows

#### 1.1. Установка через kubectl

```bash
# Создать namespace
kubectl create namespace argo

# Установить Argo Workflows
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.5.0/install.yaml

# Проверить установку
kubectl get pods -n argo
```

#### 1.2. Настройка прав доступа

```bash
# Создать ServiceAccount с правами
kubectl create rolebinding argo-admin \
  --clusterrole=admin \
  --serviceaccount=argo:argo-server \
  -n argo

# Для production используйте более ограниченные права
```

#### 1.3. Доступ к UI

```bash
# Порт-форвардинг для локального доступа
kubectl -n argo port-forward deployment/argo-server 2746:2746

# Открыть в браузере: https://localhost:2746
```

#### 1.4. Установка CLI

**Linux/macOS:**
```bash
# Скачать и установить
curl -sLO https://github.com/argoproj/argo-workflows/releases/download/v3.5.0/argo-linux-amd64.gz
gunzip argo-linux-amd64.gz
chmod +x argo-linux-amd64
sudo mv argo-linux-amd64 /usr/local/bin/argo

# Проверить
argo version
```

**Windows:**
```powershell
# Скачать с GitHub releases
# https://github.com/argoproj/argo-workflows/releases

# Добавить в PATH
$env:Path += ";C:\tools\argo"
```

---

### Шаг 2: Развертывание WorkflowTemplates

#### 2.1. Применение всех шаблонов

```bash
# Перейти в директорию проекта
cd hw11/

# Применить все шаблоны
kubectl apply -f workflow-templates.yaml -n argo

# Проверить установку
kubectl get workflowtemplates -n argo
```

Ожидаемый вывод:
```
NAME                               AGE
data-validation-template           10s
etl-processing-template           10s
notification-template             10s
conditional-execution-template    10s
batch-file-processor-template     10s
```

#### 2.2. Проверка деталей шаблона

```bash
# Посмотреть детали конкретного шаблона
kubectl describe workflowtemplate data-validation-template -n argo

# Получить YAML шаблона
kubectl get workflowtemplate data-validation-template -n argo -o yaml
```

---

### Шаг 3: Настройка окружения

#### 3.1. Настройка секретов для уведомлений

```bash
# Создать secret для Slack webhook
kubectl create secret generic slack-webhook \
  --from-literal=url=https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -n argo

# Создать secret для email
kubectl create secret generic email-credentials \
  --from-literal=smtp-server=smtp.gmail.com \
  --from-literal=smtp-port=587 \
  --from-literal=smtp-username=your-email@gmail.com \
  --from-literal=smtp-password=your-app-password \
  -n argo

# Проверить секреты
kubectl get secrets -n argo
```

#### 3.2. Настройка доступа к S3

**Вариант 1: AWS Credentials через Secret**

```bash
kubectl create secret generic aws-credentials \
  --from-literal=accessKeyID=YOUR_ACCESS_KEY \
  --from-literal=secretAccessKey=YOUR_SECRET_KEY \
  -n argo
```

**Вариант 2: IRSA (рекомендуется для production)**

```yaml
# service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: argo-workflow-sa
  namespace: argo
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/ArgoWorkflowRole
```

```bash
kubectl apply -f service-account.yaml
```

#### 3.3. Настройка ConfigMap для конфигурации

```yaml
# workflow-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: workflow-config
  namespace: argo
data:
  default-bucket: "s3://my-data-lake"
  default-region: "us-east-1"
  notification-channel: "#data-alerts"
  quality-threshold: "1000"
```

```bash
kubectl apply -f workflow-config.yaml
```

---

### Шаг 4: Запуск workflows

#### 4.1. Запуск основного пайплайна

```bash
# Запуск с параметрами по умолчанию
kubectl create -f main-workflow.yaml -n argo

# Запуск через Argo CLI
argo submit main-workflow.yaml -n argo

# Запуск с кастомными параметрами
argo submit main-workflow.yaml -n argo \
  -p input-data-path="s3://my-bucket/data/orders.csv" \
  -p processing-mode="thorough" \
  -p notification-recipients="team@company.com"
```

#### 4.2. Мониторинг выполнения

```bash
# Список всех workflows
argo list -n argo

# Статус конкретного workflow
argo get <workflow-name> -n argo

# Логи в реальном времени
argo logs -f <workflow-name> -n argo

# Логи конкретного шага
argo logs <workflow-name> <step-name> -n argo
```

#### 4.3. Управление workflows

```bash
# Остановить workflow
argo stop <workflow-name> -n argo

# Удалить workflow
argo delete <workflow-name> -n argo

# Повторить workflow
argo resubmit <workflow-name> -n argo

# Повторить только неудавшиеся шаги
argo retry <workflow-name> -n argo
```

---

### Шаг 5: Настройка автоматизации

#### 5.1. CronWorkflow для периодического запуска

```yaml
# cron-workflow.yaml
apiVersion: argoproj.io/v1alpha1
kind: CronWorkflow
metadata:
  name: daily-data-pipeline
  namespace: argo
spec:
  schedule: "0 2 * * *"  # Каждый день в 2:00 AM
  timezone: "Europe/Moscow"
  concurrencyPolicy: "Replace"
  startingDeadlineSeconds: 0
  workflowSpec:
    entrypoint: data-processing-pipeline
    arguments:
      parameters:
      - name: input-data-path
        value: "s3://data-lake/daily/{{workflow.creationTimestamp.Y}}/{{workflow.creationTimestamp.m}}/{{workflow.creationTimestamp.d}}/"
      - name: processing-mode
        value: "standard"
    # ... остальная спецификация из main-workflow.yaml
```

```bash
# Применить CronWorkflow
kubectl apply -f cron-workflow.yaml -n argo

# Посмотреть CronWorkflows
argo cron list -n argo

# Запустить вручную
argo cron create --from cronwf/daily-data-pipeline -n argo
```

#### 5.2. WorkflowEventBinding для запуска по событиям

```yaml
# event-binding.yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowEventBinding
metadata:
  name: s3-data-arrival
  namespace: argo
spec:
  event:
    selector: payload.bucket == "my-data-lake" && payload.event == "s3:ObjectCreated:*"
  submit:
    workflowTemplateRef:
      name: main-workflow
    arguments:
      parameters:
      - name: input-data-path
        valueFrom:
          event: payload.object.key
```

---

### Шаг 6: Интеграция с CI/CD

#### 6.1. GitHub Actions

```yaml
# .github/workflows/deploy-templates.yml
name: Deploy Argo Workflow Templates

on:
  push:
    branches: [main]
    paths:
      - 'hw11/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Configure kubectl
      uses: azure/k8s-set-context@v3
      with:
        method: kubeconfig
        kubeconfig: ${{ secrets.KUBE_CONFIG }}
    
    - name: Deploy templates
      run: |
        kubectl apply -f hw11/workflow-templates.yaml -n argo
    
    - name: Verify deployment
      run: |
        kubectl get workflowtemplates -n argo
```

#### 6.2. GitLab CI/CD

```yaml
# .gitlab-ci.yml
deploy-templates:
  stage: deploy
  image: bitnami/kubectl:latest
  script:
    - kubectl config set-cluster k8s --server=$K8S_SERVER
    - kubectl config set-credentials gitlab --token=$K8S_TOKEN
    - kubectl config set-context default --cluster=k8s --user=gitlab
    - kubectl config use-context default
    - kubectl apply -f hw11/workflow-templates.yaml -n argo
  only:
    - main
```

---

### Шаг 7: Настройка мониторинга

#### 7.1. Prometheus Metrics

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: argo-workflows
  namespace: argo
spec:
  selector:
    matchLabels:
      app: argo-server
  endpoints:
  - port: metrics
    interval: 30s
```

#### 7.2. Grafana Dashboard

```bash
# Импортировать dashboard для Argo Workflows
# Dashboard ID: 13927
# URL: https://grafana.com/grafana/dashboards/13927
```

#### 7.3. Алерты

```yaml
# prometheus-rules.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: argo-workflow-alerts
  namespace: argo
spec:
  groups:
  - name: argo-workflows
    interval: 30s
    rules:
    - alert: WorkflowFailed
      expr: argo_workflow_status_phase{phase="Failed"} > 0
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "Workflow {{ $labels.name }} has failed"
    
    - alert: WorkflowStuck
      expr: argo_workflow_status_phase{phase="Running"} > 0
      for: 1h
      labels:
        severity: warning
      annotations:
        summary: "Workflow {{ $labels.name }} is running for too long"
```

---

### Шаг 8: Production Best Practices

#### 8.1. Resource Limits

Добавьте resource limits в шаблоны:

```yaml
container:
  image: python:3.10-slim
  resources:
    requests:
      memory: "256Mi"
      cpu: "250m"
    limits:
      memory: "512Mi"
      cpu: "500m"
```

#### 8.2. Node Selectors

Используйте node selectors для больших задач:

```yaml
nodeSelector:
  workload-type: data-processing
tolerations:
- key: "workload"
  operator: "Equal"
  value: "data-processing"
  effect: "NoSchedule"
```

#### 8.3. Volume Claims

Для работы с большими данными:

```yaml
volumeClaimTemplates:
- metadata:
    name: workdir
  spec:
    accessModes: [ "ReadWriteOnce" ]
    resources:
      requests:
        storage: 10Gi
```

#### 8.4. Архивирование логов

```yaml
# workflow-controller-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: workflow-controller-configmap
  namespace: argo
data:
  artifactRepository: |
    archiveLogs: true
    s3:
      bucket: my-argo-logs
      endpoint: s3.amazonaws.com
      region: us-east-1
      keyFormat: "{{workflow.namespace}}/{{workflow.name}}/{{pod.name}}"
```

---

### Шаг 9: Обновление шаблонов

#### 9.1. Стратегия обновления

```bash
# Версионирование шаблонов
kubectl apply -f workflow-templates-v1.yaml -n argo
kubectl apply -f workflow-templates-v2.yaml -n argo

# Постепенная миграция workflows на новую версию
```

#### 9.2. Тестирование изменений

```bash
# Запустить в отдельном namespace для тестирования
kubectl create namespace argo-test
kubectl apply -f workflow-templates.yaml -n argo-test
kubectl create -f main-workflow.yaml -n argo-test

# После проверки применить в production
kubectl apply -f workflow-templates.yaml -n argo
```

---

### Шаг 10: Troubleshooting

#### 10.1. Частые проблемы

**Проблема: Шаблон не найден**
```bash
# Проверить namespace
kubectl get workflowtemplates -n argo

# Проверить имя в templateRef
kubectl describe workflow <name> -n argo
```

**Проблема: Недостаточно прав**
```bash
# Проверить RBAC
kubectl get rolebindings -n argo
kubectl describe rolebinding argo-admin -n argo

# Создать дополнительные права если нужно
kubectl create rolebinding argo-workflow-sa-admin \
  --clusterrole=admin \
  --serviceaccount=argo:argo-workflow-sa \
  -n argo
```

**Проблема: Pods не запускаются**
```bash
# Проверить события
kubectl get events -n argo --sort-by='.lastTimestamp'

# Проверить ресурсы node
kubectl top nodes

# Проверить resource limits
kubectl describe pod <pod-name> -n argo
```

#### 10.2. Сбор диагностической информации

```bash
# Экспорт всей конфигурации
kubectl get all -n argo -o yaml > argo-dump.yaml

# Логи workflow controller
kubectl logs -n argo deployment/workflow-controller

# Логи argo server
kubectl logs -n argo deployment/argo-server

# Описание workflow с полными деталями
argo get <workflow-name> -n argo -o yaml
```

---

### Шаг 11: Очистка

#### 11.1. Удаление workflows

```bash
# Удалить все завершенные workflows
argo delete --completed -n argo

# Удалить workflows старше 7 дней
argo delete --older 7d -n argo

# Удалить все workflows (осторожно!)
argo delete --all -n argo
```

#### 11.2. Удаление шаблонов

```bash
# Удалить конкретный шаблон
kubectl delete workflowtemplate data-validation-template -n argo

# Удалить все шаблоны
kubectl delete -f workflow-templates.yaml -n argo
```

#### 11.3. Полная деинсталляция

```bash
# Удалить все ресурсы Argo
kubectl delete namespace argo

# Удалить CRDs
kubectl delete crd workflows.argoproj.io
kubectl delete crd workflowtemplates.argoproj.io
kubectl delete crd cronworkflows.argoproj.io
```

---

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи workflow controller
2. Изучите события в namespace
3. Обратитесь к официальной документации Argo Workflows
4. Создайте issue в репозитории проекта

---

## 🔄 Обновления

Регулярно проверяйте обновления:
- Argo Workflows releases: https://github.com/argoproj/argo-workflows/releases
- Security advisories: https://github.com/argoproj/argo-workflows/security/advisories

---

## ✅ Чеклист развертывания

- [ ] Установлен Kubernetes кластер
- [ ] Установлен Argo Workflows
- [ ] Создан namespace `argo`
- [ ] Настроены RBAC права
- [ ] Установлен Argo CLI
- [ ] Применены все WorkflowTemplates
- [ ] Созданы секреты для уведомлений
- [ ] Настроен доступ к S3/storage
- [ ] Протестирован запуск примеров
- [ ] Настроен мониторинг (опционально)
- [ ] Настроены CronWorkflows (опционально)
- [ ] Документация обновлена для команды

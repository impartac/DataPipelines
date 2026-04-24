# 🐳 Docker Setup - Полное руководство для защиты проекта

## 📋 Содержание

1. [Зачем Docker?](#зачем-docker)
2. [Архитектура решения](#архитектура-решения)
3. [Компоненты системы](#компоненты-системы)
4. [Как работает setup.ps1](#как-работает-setupps1)
5. [Пошаговое объяснение](#пошаговое-объяснение)
6. [Запуск одной командой](#запуск-одной-командой)
7. [Что происходит под капотом](#что-происходит-под-капотом)
8. [Вопросы для защиты](#вопросы-для-защиты)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Зачем Docker?

### Проблемы без Docker

❌ **Без Docker-based решения:**
- Нужно устанавливать полноценный Kubernetes кластер (minikube, kind, k3s)
- Требуется много ручных команд
- Различия между окружениями разработчиков
- Сложно воспроизвести проблемы
- Долгая настройка (30-60 минут)

✅ **С Docker-based решением:**
- **Одна команда** для запуска всего окружения
- **Изолированное** окружение в контейнерах
- **Воспроизводимость** - работает одинаково на всех машинах
- **Быстро** - 5-10 минут до полной готовности
- **Легко удалить** - не засоряет систему

---

## 🏗️ Архитектура решения

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ВАША МАШИНА (Windows)                        │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      Docker Desktop                           │   │
│  │                                                                │   │
│  │  ┌──────────────────────────────────────────────────────┐    │   │
│  │  │           k3d (Kubernetes in Docker)                 │    │   │
│  │  │                                                        │    │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │   │
│  │  │  │  Server  │  │  Agent 1 │  │  Agent 2 │          │    │   │
│  │  │  │  Node    │  │  Node    │  │  Node    │          │    │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘          │    │   │
│  │  │       │              │              │                │    │   │
│  │  │       └──────────────┴──────────────┘                │    │   │
│  │  │                      │                                │    │   │
│  │  │        ┌─────────────┴─────────────┐                 │    │   │
│  │  │        │                           │                 │    │   │
│  │  │  ┌─────▼──────┐           ┌───────▼────────┐        │    │   │
│  │  │  │   Argo     │           │   Argo         │        │    │   │
│  │  │  │  Workflows │           │   Server       │        │    │   │
│  │  │  │  Controller│           │   (UI + API)   │        │    │   │
│  │  │  └────────────┘           └────────────────┘        │    │   │
│  │  │                                  │                    │    │   │
│  │  └──────────────────────────────────┼───────────────────┘    │   │
│  │                                     │                         │   │
│  │  ┌──────────────────────────────────┼───────────────────┐    │   │
│  │  │     Docker Compose Services      │                   │    │   │
│  │  │                                  │                   │    │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──▼───────┐          │    │   │
│  │  │  │  MinIO   │  │PostgreSQL│  │ MailHog  │          │    │   │
│  │  │  │   (S3)   │  │  (Meta)  │  │  (SMTP)  │          │    │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘          │    │   │
│  │  └──────────────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Ваш Браузер                               │   │
│  │              http://localhost:2746                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
```

### Почему именно k3d?

**k3d** = k3s (легковесный Kubernetes) + Docker

**Альтернативы:**
- **minikube** - тяжелее, требует VM или Docker
- **kind** (Kubernetes in Docker) - похож на k3d, но k3d проще в использовании
- **k3s** - нужно устанавливать на host систему
- **Docker Desktop Kubernetes** - работает, но медленнее и менее настраиваемый

**Преимущества k3d:**
1. ✅ Работает полностью в Docker контейнерах
2. ✅ Легковесный (k3s использует меньше памяти чем полный Kubernetes)
3. ✅ Быстрый запуск (30-60 секунд)
4. ✅ Легко создавать/удалять кластеры
5. ✅ Поддержка LoadBalancer из коробки
6. ✅ Отличная интеграция с локальным Docker registry

---

## 🧩 Компоненты системы

### 1. **setup.ps1** - Главный скрипт автоматизации

**Что делает:**
```powershell
# 1. Проверяет предварительные требования
Test-Prerequisites
  └─> Docker установлен и запущен?
  
# 2. Устанавливает инструменты (если нужно)
Install-Dependencies
  ├─> Chocolatey (пакетный менеджер для Windows)
  ├─> kubectl (CLI для Kubernetes)
  ├─> k3d (создание кластеров)
  └─> argo (CLI для Argo Workflows)
  
# 3. Создает Kubernetes кластер
New-K3dCluster
  └─> k3d cluster create argo-workflows
      ├─> 1 server node (control plane)
      ├─> 2 agent nodes (workers)
      └─> Port forwarding: 2746 для UI
      
# 4. Устанавливает Argo Workflows
Install-ArgoWorkflows
  ├─> kubectl create namespace argo
  ├─> kubectl apply -f argo-install.yaml
  └─> Ждет готовности всех подов
  
# 5. Применяет ваши WorkflowTemplates
Deploy-WorkflowTemplates
  └─> kubectl apply -f workflow-templates.yaml
  
# 6. Настраивает UI
Enable-ArgoUI
  ├─> Меняет Service type на LoadBalancer
  ├─> Отключает авторизацию (для локальной разработки)
  └─> Открывает доступ на http://localhost:2746
```

**Параметры скрипта:**
```powershell
# Пропустить установку зависимостей
.\setup.ps1 -SkipInstall

# Удалить и создать кластер заново
.\setup.ps1 -CleanStart

# Запустить примеры после установки
.\setup.ps1 -RunExamples

# Подробный вывод
.\setup.ps1 -Verbose

# Комбинация параметров
.\setup.ps1 -CleanStart -RunExamples
```

### 2. **docker-compose.yml** - Вспомогательные сервисы

**Зачем нужен:**
- Argo Workflows работает в Kubernetes (k3d)
- Но для полноценной работы нужны дополнительные сервисы
- docker-compose запускает их отдельно

**Сервисы:**

#### MinIO (S3-совместимое хранилище)
```yaml
Назначение: Хранение артефактов workflows
Порты: 9000 (API), 9001 (Console)
Доступ: http://localhost:9001
Логин: minioadmin / minioadmin
```

**Почему MinIO?**
- Workflows часто создают файлы (артефакты)
- Нужно где-то их хранить
- MinIO = локальный S3, не нужен AWS

#### PostgreSQL
```yaml
Назначение: Хранение метаданных workflows (опционально)
Порт: 5432
База: argo
Логин: argo / argo_password
```

**Зачем PostgreSQL?**
- По умолчанию Argo хранит данные в Kubernetes (etcd)
- Для production лучше использовать PostgreSQL
- Быстрее поиск, лучше масштабируемость

#### MailHog
```yaml
Назначение: Тестовый SMTP сервер
Порты: 1025 (SMTP), 8025 (Web UI)
Доступ: http://localhost:8025
```

**Зачем MailHog?**
- Для тестирования email уведомлений
- Перехватывает все письма
- Можно посмотреть в веб-интерфейсе

#### Redis
```yaml
Назначение: Кэш и очереди
Порт: 6379
```

**Зачем Redis?**
- Ускорение работы workflows
- Хранение временных данных
- Синхронизация между workflows

---

## 🔄 Как работает setup.ps1

### Детальный разбор по шагам

#### Шаг 1: Проверка Docker

```powershell
function Test-Prerequisites {
    # 1. Проверяем что Docker установлен
    if (Test-CommandExists "docker") {
        # 2. Проверяем что Docker запущен
        docker ps 2>&1
        # 3. Если не запущен - ошибка
    }
}
```

**Что проверяется:**
- ✅ Docker Desktop установлен
- ✅ Docker daemon запущен
- ✅ Можем выполнять команды docker

**Почему важно:**
- k3d требует работающий Docker
- Без Docker ничего не заработает

#### Шаг 2: Установка инструментов

```powershell
function Install-Dependencies {
    # 1. Chocolatey (если нет)
    if (-not (Test-CommandExists "choco")) {
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString(
            'https://community.chocolatey.org/install.ps1'
        ))
    }
    
    # 2. kubectl
    choco install kubernetes-cli -y
    
    # 3. k3d
    choco install k3d -y
    
    # 4. Argo CLI
    # Скачиваем с GitHub releases
    $argoUrl = "https://github.com/argoproj/argo-workflows/releases/download/v3.5.5/argo-windows-amd64.gz"
    Invoke-WebRequest -Uri $argoUrl -OutFile "argo.gz"
    # Распаковываем и устанавливаем
}
```

**Что устанавливается:**

| Инструмент | Назначение | Команды |
|------------|-----------|---------|
| **kubectl** | Управление Kubernetes | `kubectl get pods` |
| **k3d** | Создание кластеров | `k3d cluster create` |
| **argo** | Управление workflows | `argo submit`, `argo logs` |

**Почему Chocolatey:**
- Пакетный менеджер для Windows (аналог apt/yum)
- Упрощает установку инструментов
- Автоматически обновляет PATH

#### Шаг 3: Создание Kubernetes кластера

```powershell
function New-K3dCluster {
    # Создаем кластер с именем "argo-workflows"
    k3d cluster create argo-workflows `
        --api-port 6550 `              # API server порт
        --port "2746:2746@loadbalancer" ` # Проброс порта для UI
        --agents 2 `                   # 2 worker nodes
        --wait                         # Ждать готовности
}
```

**Что создается:**

```
Kubernetes кластер "argo-workflows"
├── Server Node (control plane)
│   ├── API Server (порт 6550)
│   ├── Scheduler
│   ├── Controller Manager
│   └── etcd (хранилище)
│
├── Agent Node 1 (worker)
│   └── Kubelet (запускает поды)
│
└── Agent Node 2 (worker)
    └── Kubelet (запускает поды)
```

**Архитектура k3d:**

```
┌─────────────────────────────────────────────────┐
│              Docker Container 1                  │
│          k3s-argo-workflows-server-0            │
│                                                   │
│  ┌────────────────────────────────────────┐     │
│  │      Kubernetes Control Plane          │     │
│  │  ┌──────────┐  ┌──────────────────┐   │     │
│  │  │API Server│  │  Scheduler       │   │     │
│  │  └──────────┘  └──────────────────┘   │     │
│  │  ┌──────────┐  ┌──────────────────┐   │     │
│  │  │   etcd   │  │Controller Manager│   │     │
│  │  └──────────┘  └──────────────────┘   │     │
│  └────────────────────────────────────────┘     │
└───────────────────────────────────────────────────┘
         │                           │
         ├──────────────┬────────────┘
         │              │
┌────────▼─────┐  ┌────▼─────────┐
│  Container 2  │  │ Container 3  │
│  Agent Node 1 │  │ Agent Node 2 │
│               │  │              │
│  ┌─────────┐  │  │  ┌─────────┐ │
│  │ Kubelet │  │  │  │ Kubelet │ │
│  └─────────┘  │  │  └─────────┘ │
└───────────────┘  └──────────────┘
```

**Почему 2 agent nodes:**
- Демонстрация распределенной обработки
- Workflows могут выполняться параллельно
- Closer к production окружению

**Port forwarding:**
```
--port "2746:2746@loadbalancer"
```
- Порт 2746 (Argo UI) доступен на localhost:2746
- Трафик идет через LoadBalancer
- Не нужно делать port-forward вручную

#### Шаг 4: Установка Argo Workflows

```powershell
function Install-ArgoWorkflows {
    # 1. Создаем namespace
    kubectl create namespace argo
    
    # 2. Применяем манифест
    kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.5.5/install.yaml
    
    # 3. Ждем готовности подов
    kubectl wait --for=condition=Ready pods --all -n argo --timeout=120s
    
    # 4. Настраиваем права
    kubectl create rolebinding default-admin \
        --clusterrole=admin \
        --serviceaccount=argo:default \
        -n argo
}
```

**Что устанавливается:**

```
Namespace: argo
│
├── Deployment: argo-server
│   └── Pod: argo-server-xxxxx
│       ├── Container: argo-server
│       │   ├── Web UI (порт 2746)
│       │   └── API Server
│       └── Volume: tmp
│
├── Deployment: workflow-controller
│   └── Pod: workflow-controller-xxxxx
│       └── Container: workflow-controller
│           ├── Следит за Workflow ресурсами
│           ├── Создает поды для выполнения steps
│           └── Управляет жизненным циклом
│
├── ServiceAccount: argo
├── ServiceAccount: argo-server
│
└── Service: argo-server
    ├── Type: ClusterIP (потом меняем на LoadBalancer)
    └── Port: 2746
```

**Как работает Argo Workflows:**

```
1. Вы создаете Workflow:
   kubectl create -f main-workflow.yaml

2. Kubernetes сохраняет Workflow как CRD ресурс

3. Workflow Controller видит новый Workflow:
   ┌────────────────────────────┐
   │  Workflow Controller       │
   │  (постоянно следит за CRD) │
   └────────────────────────────┘
              │
              ▼
   Читает Workflow спецификацию
              │
              ▼
   Создает поды для каждого step:
   ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ Pod 1   │  │ Pod 2   │  │ Pod 3   │
   │ (step1) │  │ (step2) │  │ (step3) │
   └─────────┘  └─────────┘  └─────────┘
              │
              ▼
   Следит за выполнением
              │
              ▼
   Обновляет статус Workflow

4. Вы можете смотреть статус:
   - kubectl get workflow -n argo
   - argo list -n argo
   - UI: http://localhost:2746
```

#### Шаг 5: Применение WorkflowTemplates

```powershell
function Deploy-WorkflowTemplates {
    # Применяем наши шаблоны
    kubectl apply -f workflow-templates.yaml -n argo
    
    # Показываем список
    kubectl get workflowtemplate -n argo
}
```

**Что происходит:**

```yaml
# workflow-templates.yaml содержит 5 шаблонов:

apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: data-validation-template
  namespace: argo
spec:
  # ... спецификация шаблона

---
# еще 4 шаблона...
```

**Kubernetes создает ресурсы:**

```
$ kubectl get workflowtemplate -n argo

NAME                            AGE
data-validation-template        5s
etl-processing-template         5s
notification-template           5s
conditional-execution-template  5s
batch-file-processor-template   5s
```

**Эти шаблоны теперь можно использовать:**

```yaml
# main-workflow.yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: data-pipeline
spec:
  templates:
  - name: validate
    templateRef:
      name: data-validation-template  # ← ссылка на шаблон
      template: validate-data
```

#### Шаг 6: Настройка UI

```powershell
function Enable-ArgoUI {
    # 1. Меняем тип сервиса на LoadBalancer
    kubectl patch svc argo-server -n argo \
        -p '{"spec": {"type": "LoadBalancer"}}'
    
    # 2. Отключаем авторизацию (только для локальной разработки!)
    kubectl patch deployment argo-server -n argo --type='json' \
        -p='[{"op": "replace", 
              "path": "/spec/template/spec/containers/0/args", 
              "value": ["server", "--auth-mode=server"]}]'
    
    # 3. Ждем перезапуска пода
    kubectl wait --for=condition=Ready pods \
        -l app=argo-server -n argo --timeout=60s
}
```

**Что меняется:**

**До:**
```yaml
Service: argo-server
  type: ClusterIP  # доступен только внутри кластера
  port: 2746
```

**После:**
```yaml
Service: argo-server
  type: LoadBalancer  # доступен снаружи
  port: 2746
  # k3d автоматически пробрасывает на localhost:2746
```

**Авторизация:**
- По умолчанию Argo требует токен
- `--auth-mode=server` отключает это
- **ВАЖНО:** Только для локальной разработки!
- В production используйте SSO или токены

---

## 🚀 Запуск одной командой

### Вариант 1: Полная автоматическая установка

```powershell
# Клонируйте репозиторий и перейдите в hw11
cd hw11

# Запустите установку
.\setup.ps1
```

**Что произойдет:**
1. ✅ Проверка Docker (5 секунд)
2. ✅ Установка зависимостей (2-3 минуты, только первый раз)
3. ✅ Создание кластера (1-2 минуты)
4. ✅ Установка Argo Workflows (1-2 минуты)
5. ✅ Применение шаблонов (10 секунд)
6. ✅ Настройка UI (30 секунд)

**Общее время: 5-10 минут**

### Вариант 2: С примерами

```powershell
.\setup.ps1 -RunExamples
```

Дополнительно запускает main-workflow после установки.

### Вариант 3: Чистая установка

```powershell
.\setup.ps1 -CleanStart -RunExamples
```

Удаляет старый кластер (если есть) и создает новый.

### Вариант 4: Быстрый перезапуск

```powershell
# Если зависимости уже установлены
.\setup.ps1 -SkipInstall -CleanStart
```

---

## 🔍 Что происходит под капотом

### Подробная timeline выполнения

```
T+0:00  🔍 Проверка Docker
        ├─> docker --version
        └─> docker ps (проверка daemon)

T+0:05  📦 Установка зависимостей
        ├─> Chocolatey (если нужно)
        ├─> kubectl via chocolatey
        ├─> k3d via chocolatey
        └─> argo CLI (скачивание с GitHub)

T+2:00  🚀 Создание кластера
        ├─> k3d cluster create argo-workflows
        │   ├─> Создание Docker network
        │   ├─> Запуск server node (контейнер)
        │   ├─> Запуск agent node 1 (контейнер)
        │   ├─> Запуск agent node 2 (контейнер)
        │   └─> Настройка kubeconfig
        └─> Проверка готовности узлов

T+4:00  ☸️ Установка Argo
        ├─> kubectl create namespace argo
        ├─> kubectl apply -f install.yaml
        │   ├─> CustomResourceDefinitions (Workflow, WorkflowTemplate, etc)
        │   ├─> ServiceAccounts
        │   ├─> Roles & RoleBindings
        │   ├─> Deployments (controller, server)
        │   └─> Services
        └─> kubectl wait --for=condition=Ready pods

T+6:00  📋 Применение шаблонов
        └─> kubectl apply -f workflow-templates.yaml
            ├─> data-validation-template
            ├─> etl-processing-template
            ├─> notification-template
            ├─> conditional-execution-template
            └─> batch-file-processor-template

T+6:30  🌐 Настройка UI
        ├─> kubectl patch svc (LoadBalancer)
        ├─> kubectl patch deployment (--auth-mode=server)
        └─> kubectl wait (готовность пода)

T+7:00  ✅ Готово!
        └─> Открытие браузера http://localhost:2746
```

### Сетевая схема

```
┌─────────────────────────────────────────────────────────────┐
│                    Ваша машина                               │
│                                                               │
│  ┌──────────────────┐                                        │
│  │  PowerShell      │                                        │
│  │  .\setup.ps1     │                                        │
│  └────────┬─────────┘                                        │
│           │                                                   │
│           ▼                                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               Docker Desktop                          │   │
│  │                                                        │   │
│  │  ┌──────────────────────────────────────────────┐    │   │
│  │  │  Docker Bridge Network: bridge               │    │   │
│  │  │  Subnet: 172.17.0.0/16                       │    │   │
│  │  └──────────────────────────────────────────────┘    │   │
│  │                                                        │   │
│  │  ┌──────────────────────────────────────────────┐    │   │
│  │  │  k3d Network: k3d-argo-workflows             │    │   │
│  │  │  Subnet: 172.18.0.0/16                       │    │   │
│  │  │                                               │    │   │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐      │    │   │
│  │  │  │Server   │  │Agent 1  │  │Agent 2  │      │    │   │
│  │  │  │172.18.  │  │172.18.  │  │172.18.  │      │    │   │
│  │  │  │  0.2    │  │  0.3    │  │  0.4    │      │    │   │
│  │  │  └─────────┘  └─────────┘  └─────────┘      │    │   │
│  │  └──────────────────────────────────────────────┘    │   │
│  │                                                        │   │
│  │  ┌──────────────────────────────────────────────┐    │   │
│  │  │  Argo Network: argo-network                  │    │   │
│  │  │  Subnet: 172.20.0.0/16                       │    │   │
│  │  │                                               │    │   │
│  │  │  ┌──────┐  ┌────────┐  ┌────────┐  ┌──────┐ │    │   │
│  │  │  │MinIO │  │Postgres│  │MailHog │  │Redis │ │    │   │
│  │  │  └──────┘  └────────┘  └────────┘  └──────┘ │    │   │
│  │  └──────────────────────────────────────────────┘    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  Port Forwarding:                                            │
│  localhost:2746  ──> 172.18.0.2:2746 (Argo UI)             │
│  localhost:6550  ──> 172.18.0.2:6443 (K8s API)             │
│  localhost:9000  ──> 172.20.0.2:9000 (MinIO API)           │
│  localhost:9001  ──> 172.20.0.2:9001 (MinIO Console)       │
│  localhost:8025  ──> 172.20.0.4:8025 (MailHog UI)          │
└─────────────────────────────────────────────────────────────┘
```

### Взаимодействие компонентов

```
┌──────────────┐
│   kubectl    │ Вы запускаете: kubectl create -f main-workflow.yaml
└──────┬───────┘
       │ HTTP POST
       ▼
┌──────────────────┐
│  Kubernetes API  │ Сохраняет Workflow как Custom Resource
│  Server          │
└──────┬───────────┘
       │ Watch
       ▼
┌───────────────────────┐
│ Workflow Controller   │ Видит новый Workflow
│ (argo-controller)     │
└──────┬────────────────┘
       │
       ├─> Читает спецификацию Workflow
       │
       ├─> Определяет первый step для выполнения
       │
       ├─> Создает Pod для step:
       │   POST /api/v1/namespaces/argo/pods
       │   
       ▼
┌──────────────────┐
│  Kubelet         │ Получает команду запустить Pod
│  (на Agent Node) │
└──────┬───────────┘
       │
       ├─> Скачивает Docker image (если нужно)
       │
       ├─> Создает контейнер
       │
       ├─> Запускает команду/скрипт
       │   
       ▼
┌──────────────────┐
│  Container       │ Выполняется код вашего step
│  (step pod)      │ (например, Python скрипт валидации)
└──────┬───────────┘
       │
       ├─> Пишет логи (видны через kubectl logs)
       │
       ├─> Завершается (exit code 0 или 1)
       │
       ▼
┌───────────────────────┐
│ Workflow Controller   │ Видит что Pod завершился
└──────┬────────────────┘
       │
       ├─> Обновляет статус step в Workflow
       │
       ├─> Определяет следующий step
       │
       └─> Повторяет процесс для следующего step

                    ▼
            (все steps выполнены)
                    │
                    ▼
┌───────────────────────────┐
│ Workflow Controller       │ Обновляет статус Workflow на "Succeeded"
└───────────────────────────┘

┌──────────────┐
│  Argo UI     │ Показывает статус в реальном времени
│ (веб браузер)│ http://localhost:2746
└──────────────┘
```

---

## 💬 Вопросы для защиты

### Блок 1: Общие вопросы об архитектуре

**Q: Почему вы выбрали Docker-based решение?**

**A:** Docker-based решение имеет несколько критических преимуществ:

1. **Воспроизводимость** - одинаково работает на любой машине с Docker
2. **Изоляция** - не засоряет основную систему
3. **Скорость** - полная установка за 5-10 минут
4. **Удобство** - удалить все можно одной командой
5. **Реалистичность** - в production тоже используется Kubernetes в контейнерах

**Q: Что такое k3d и почему не minikube?**

**A:** 
- **k3d** = k3s в Docker контейнерах
- **k3s** = облегченный Kubernetes от Rancher (занимает <512MB RAM)
- **Преимущества перед minikube:**
  - Легче (меньше ресурсов)
  - Быстрее запускается (30-60 сек vs 2-3 мин)
  - Нативная поддержка LoadBalancer
  - Легче создавать multi-node кластеры
  - Ближе к production (k3s часто используется в edge/IoT)

**Q: Объясните что происходит когда вы запускаете `.\setup.ps1`**

**A:** Скрипт выполняет 6 основных шагов:

1. **Проверка предварительных требований** - Docker установлен и запущен
2. **Установка зависимостей** - kubectl, k3d, argo CLI (если нет)
3. **Создание кластера** - k3d создает 3 Docker контейнера (1 server + 2 agents)
4. **Установка Argo Workflows** - применяет манифест из GitHub releases
5. **Применение шаблонов** - загружает наши 5 WorkflowTemplates
6. **Настройка UI** - делает Argo UI доступным на localhost:2746

### Блок 2: Kubernetes и Argo

**Q: Как Argo Workflows запускает ваши задачи?**

**A:** Workflow Controller следит за Workflow ресурсами и для каждого step:

1. Создает новый Pod в Kubernetes
2. Pod запускает Docker container с нужным image
3. В контейнере выполняется команда/скрипт
4. Controller следит за статусом Pod
5. После завершения Pod, Controller переходит к следующему step

**Q: Что такое WorkflowTemplate и чем отличается от Workflow?**

**A:**

| | WorkflowTemplate | Workflow |
|---|---|---|
| **Назначение** | Переиспользуемый шаблон | Конкретный запуск |
| **Хранится** | Постоянно в кластере | Удаляется после TTL |
| **Можно запускать** | Нет (это template) | Да |
| **Аналогия** | Функция в коде | Вызов функции |

```yaml
# WorkflowTemplate - это как функция
kind: WorkflowTemplate
metadata:
  name: my-template
spec:
  templates:
  - name: my-task
    inputs:
      parameters:
      - name: data
    ...

# Workflow - это как вызов функции
kind: Workflow
spec:
  templates:
  - name: use-template
    templateRef:
      name: my-template  # вызываем template
      template: my-task
    arguments:
      parameters:
      - name: data
        value: "test.csv"
```

**Q: Какие компоненты входят в Argo Workflows?**

**A:**

1. **Workflow Controller** - основной компонент
   - Следит за Workflow ресурсами
   - Создает Pods для выполнения
   - Управляет жизненным циклом

2. **Argo Server** - веб сервер
   - API для работы с workflows
   - Web UI для визуализации
   - Webhook endpoints

3. **CLI (argo)** - утилита командной строки
   - `argo submit` - запустить workflow
   - `argo list` - список workflows
   - `argo logs` - смотреть логи

### Блок 3: Ваши шаблоны

**Q: Какие 5 универсальных шаблонов вы создали?**

**A:**

1. **data-validation-template**
   - Валидация данных (schema, null checks, duplicates)
   - Поддержка CSV, JSON, Parquet, Avro

2. **etl-processing-template**
   - 4 типа трансформаций: filter, aggregate, join, enrich
   - Работа с разными источниками данных

3. **notification-template**
   - Мультиканальные уведомления
   - Slack, Email, Teams, Webhook

4. **conditional-execution-template**
   - Условная логика выполнения
   - 4 типа проверок, 8 операторов

5. **batch-file-processor-template**
   - Параллельная обработка файлов
   - 5 операций: analyze, transform, compress, archive, validate

**Q: Почему эти шаблоны универсальные?**

**A:**

1. **Параметризованные** - все настраивается через inputs
2. **Независимые** - можно использовать отдельно или комбинировать
3. **Переиспользуемые** - один шаблон для разных workflows
4. **Расширяемые** - легко добавить новые функции
5. **Production-ready** - error handling, retries, timeouts

**Q: Покажите пример как использовать ваш шаблон**

**A:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  name: validate-my-data
spec:
  entrypoint: main
  templates:
  - name: main
    steps:
    - - name: validate
        templateRef:
          name: data-validation-template  # ссылка на шаблон
          template: validate-data
        arguments:
          parameters:
          - name: data_path
            value: "s3://my-bucket/data.csv"
          - name: data_format
            value: "csv"
          - name: validation_rules
            value: |
              {
                "check_schema": true,
                "check_nulls": true,
                "required_columns": ["id", "name", "date"],
                "allowed_null_rate": 0.05
              }
```

### Блок 4: Docker Compose

**Q: Зачем нужен docker-compose.yml если есть k3d?**

**A:**

- **k3d** запускает Kubernetes кластер и Argo Workflows
- **docker-compose** запускает вспомогательные сервисы:
  - MinIO (S3 storage для артефактов)
  - PostgreSQL (метаданные workflows)
  - MailHog (тестирование email)
  - Redis (кэш и очереди)

Эти сервисы не обязательны для работы Argo, но делают систему более полнофункциональной.

**Q: Как workflows взаимодействуют с MinIO?**

**A:**

```yaml
# В workflow указываем artifact
spec:
  templates:
  - name: generate-report
    outputs:
      artifacts:
      - name: report
        path: /tmp/report.pdf
        s3:
          endpoint: minio:9000
          bucket: argo-artifacts
          key: "reports/{{workflow.name}}/report.pdf"
          accessKeySecret:
            name: minio-credentials
            key: accesskey
```

Argo автоматически загружает артефакты в MinIO после завершения task.

### Блок 5: Production

**Q: Можно ли использовать это в production?**

**A:**

**Текущее решение - для локальной разработки:**
- ❌ Auth отключена (`--auth-mode=server`)
- ❌ Данные хранятся в контейнерах (ephemeral)
- ❌ Нет SSL/TLS

**Для production нужно:**
1. ✅ Включить авторизацию (SSO, tokens)
2. ✅ Использовать persistent volumes
3. ✅ Настроить HTTPS
4. ✅ Использовать внешний PostgreSQL
5. ✅ Настроить мониторинг (Prometheus)
6. ✅ Backup стратегия

**Q: Как масштабируется Argo Workflows?**

**A:**

1. **Горизонтальное масштабирование:**
   - Увеличить количество agent nodes в кластере
   - Workflows автоматически распределяются
   - Можно запускать 100+ workflows параллельно

2. **Вертикальное масштабирование:**
   - Увеличить ресурсы для workflow-controller
   - Использовать более мощные ноды

3. **Оптимизация:**
   - Workflow executor (различные типы: docker, k8sapi, pns)
   - Artifact repository оптимизация
   - Caching стратегии

---

## 🐛 Troubleshooting

### Проблема: Docker не запускается

**Ошибка:**
```
Cannot connect to the Docker daemon. Is the docker daemon running?
```

**Решение:**
1. Запустите Docker Desktop
2. Подождите пока Docker полностью запустится (индикатор в трее)
3. Проверьте: `docker ps`

### Проблема: k3d кластер не создается

**Ошибка:**
```
ERRO[0000] Failed to create cluster 'argo-workflows'
```

**Решение:**
```powershell
# Удалить старый кластер (если есть)
k3d cluster delete argo-workflows

# Проверить что Docker работает
docker ps

# Создать заново
.\setup.ps1 -CleanStart
```

### Проблема: Argo UI недоступен

**Решение:**
```powershell
# Проверить статус подов
kubectl get pods -n argo

# Проверить сервис
kubectl get svc -n argo

# Проверить логи
kubectl logs -n argo -l app=argo-server

# Перезапустить UI
kubectl rollout restart deployment argo-server -n argo
```

### Проблема: Workflows не запускаются

**Решение:**
```powershell
# Проверить права
kubectl get rolebinding -n argo

# Проверить логи controller
kubectl logs -n argo -l app=workflow-controller

# Проверить events
kubectl get events -n argo --sort-by='.lastTimestamp'
```

### Проблема: Порт 2746 занят

**Решение:**
```powershell
# Найти процесс
netstat -ano | findstr :2746

# Убить процесс (замените PID)
taskkill /PID <PID> /F

# Или использовать другой порт
k3d cluster create argo-workflows --port "8080:2746@loadbalancer"
```

---

## 📚 Дополнительные ресурсы

### Официальная документация

- **Argo Workflows:** https://argo-workflows.readthedocs.io/
- **k3d:** https://k3d.io/
- **k3s:** https://k3s.io/
- **Kubernetes:** https://kubernetes.io/docs/

### Полезные команды

```powershell
# Управление кластером
k3d cluster list
k3d cluster start argo-workflows
k3d cluster stop argo-workflows
k3d cluster delete argo-workflows

# Kubernetes
kubectl get all -n argo
kubectl describe workflow <name> -n argo
kubectl logs -n argo <pod-name>

# Argo CLI
argo list -n argo
argo get <workflow-name> -n argo
argo logs <workflow-name> -n argo --follow
argo delete <workflow-name> -n argo

# Docker Compose
docker-compose up -d      # Запустить сервисы
docker-compose ps         # Статус
docker-compose logs       # Логи
docker-compose down       # Остановить
```

---

## ✅ Checklist для защиты

### Подготовка к защите

- [ ] Понимаю зачем нужен Docker
- [ ] Могу объяснить что такое k3d
- [ ] Знаю архитектуру решения
- [ ] Понимаю как работает setup.ps1
- [ ] Могу объяснить каждый из 5 шаблонов
- [ ] Знаю разницу между Workflow и WorkflowTemplate
- [ ] Понимаю как Argo запускает задачи
- [ ] Могу показать работу в UI
- [ ] Знаю как дебажить проблемы
- [ ] Понимаю что нужно для production

### Демонстрация

- [ ] Запустить `.\setup.ps1`
- [ ] Показать кластер: `kubectl get nodes`
- [ ] Показать шаблоны: `kubectl get workflowtemplate -n argo`
- [ ] Запустить workflow: `kubectl create -f main-workflow.yaml -n argo`
- [ ] Открыть UI: http://localhost:2746
- [ ] Показать логи: `argo logs -n argo @latest`
- [ ] Объяснить что происходит на каждом этапе

---

## 🎉 Заключение

### Что вы получили

✅ **Автоматизированное решение:**
- Одна команда для запуска
- Все зависимости устанавливаются автоматически
- Готово к использованию за 5-10 минут

✅ **Production-like окружение:**
- Kubernetes кластер (k3d)
- Argo Workflows с UI
- Вспомогательные сервисы (MinIO, PostgreSQL, etc)

✅ **5 универсальных шаблонов:**
- Валидация данных
- ETL обработка
- Уведомления
- Условное выполнение
- Пакетная обработка

✅ **Полная документация:**
- Понимание архитектуры
- Объяснение каждого компонента
- Готовые ответы для защиты

### Следующие шаги

1. **Запустите установку:** `.\setup.ps1`
2. **Изучите UI:** http://localhost:2746
3. **Запустите примеры:** `kubectl create -f main-workflow.yaml -n argo`
4. **Прочитайте логи:** `argo logs -n argo @latest --follow`
5. **Экспериментируйте:** Создайте свой workflow!

**Удачи на защите! 🚀**

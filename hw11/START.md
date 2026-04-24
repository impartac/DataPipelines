# 🚀 БЫСТРЫЙ СТАРТ - 1 КОМАНДА

## Что это?

5 универсальных WorkflowTemplates для Argo Workflows, которые запускаются **одной командой** через Docker.

---

## ⚡ Запуск (5 минут)

### Требования

- ✅ Windows 10/11
- ✅ Docker Desktop (установлен и запущен)

### Команды

```powershell
# 1. Перейдите в папку проекта
cd hw11

# 2. Запустите установку
.\setup.ps1

# ВСЁ! 🎉
```

**Что установится автоматически:**
- Локальный Kubernetes кластер (k3d)
- Argo Workflows с UI
- 5 универсальных WorkflowTemplates
- Все необходимые инструменты (kubectl, k3d, argo CLI)

---

## 🌐 Доступ к UI

После установки откройте в браузере:

```
http://localhost:2746
```

Здесь вы увидите все workflows в красивом интерфейсе.

---

## 📝 Запуск примера

```powershell
# Запустить основной data pipeline
kubectl create -f main-workflow.yaml -n argo

# Посмотреть статус
kubectl get workflows -n argo

# Посмотреть логи
argo logs -n argo @latest --follow
```

---

## 🎯 Что дальше?

### Для быстрого ознакомления
📖 **[QUICKSTART.md](QUICKSTART.md)** - быстрый обзор шаблонов и примеры

### Для защиты проекта
📚 **[DOCKER_SETUP.md](DOCKER_SETUP.md)** - полное объяснение архитектуры и компонентов

### Для детального изучения
📖 **[README.md](README.md)** - полная документация всех шаблонов

---

## 🛑 Остановка и удаление

```powershell
# Остановить кластер (данные сохранятся)
k3d cluster stop argo-workflows

# Запустить снова
k3d cluster start argo-workflows

# Полностью удалить всё
k3d cluster delete argo-workflows
```

---

## ❓ Проблемы?

### Docker не запускается
1. Откройте Docker Desktop
2. Подождите пока индикатор станет зеленым
3. Запустите `.\setup.ps1` снова

### Порт 2746 занят
```powershell
# Найдите процесс
netstat -ano | findstr :2746

# Убейте процесс (замените PID)
taskkill /PID <PID> /F

# Запустите снова
.\setup.ps1 -CleanStart
```

### Что-то пошло не так
```powershell
# Полная переустановка
k3d cluster delete argo-workflows
.\setup.ps1 -CleanStart
```

---

## 📊 Что включено?

### 5 Универсальных WorkflowTemplates

1. **Data Validation** - Проверка корректности данных
2. **ETL Processing** - Extract-Transform-Load операции
3. **Notification Sender** - Уведомления (Slack, Email, Teams)
4. **Conditional Execution** - Условная логика выполнения
5. **Batch File Processor** - Пакетная обработка файлов

### Основной Workflow

**main-workflow.yaml** - Полный data processing pipeline:
```
Start → Validate → ETL → Quality Check → Batch Processing → Notify
```

### 6 Примеров

**examples.yaml** - Рабочие примеры использования каждого шаблона

---

## 🎓 Для защиты проекта

Изучите эти файлы по порядку:

1. **[DOCKER_SETUP.md](DOCKER_SETUP.md)** (30 мин)
   - Архитектура решения
   - Как работает каждый компонент
   - Ответы на вопросы для защиты

2. **[ARCHITECTURE.md](ARCHITECTURE.md)** (15 мин)
   - Диаграммы архитектуры
   - Потоки данных
   - Интеграции

3. **[REFERENCE.md](REFERENCE.md)** (10 мин)
   - Все параметры шаблонов
   - Справочные таблицы

---

## ✅ Чеклист для защиты

- [ ] Запустил `.\setup.ps1` и всё работает
- [ ] Открыл UI на http://localhost:2746
- [ ] Запустил main-workflow.yaml
- [ ] Прочитал DOCKER_SETUP.md
- [ ] Понимаю что такое k3d и Argo Workflows
- [ ] Могу объяснить каждый из 5 шаблонов
- [ ] Знаю как работает архитектура

---

## 💡 Полезные команды

```powershell
# Показать все workflows
kubectl get workflows -n argo

# Показать все шаблоны
kubectl get workflowtemplates -n argo

# Запустить workflow
kubectl create -f main-workflow.yaml -n argo

# Логи последнего workflow
argo logs -n argo @latest --follow

# Удалить все workflows
kubectl delete workflows --all -n argo

# Статус кластера
kubectl get nodes
kubectl get pods -n argo
```

---

## 🎉 Готово!

Теперь у вас есть:
- ✅ Работающее окружение Argo Workflows
- ✅ 5 универсальных шаблонов
- ✅ Примеры использования
- ✅ Полная документация

**Удачи на защите! 🚀**

---

**Проект:** HSE Data Pipelines - Homework 11  
**Автор:** Студент HSE  
**Дата:** Апрель 2026

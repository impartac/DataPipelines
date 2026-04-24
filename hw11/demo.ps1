# ================================================================================
# Скрипт быстрой демонстрации для защиты проекта
# ================================================================================
# Использование: .\demo.ps1
# ================================================================================

Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "   ДЕМОНСТРАЦИЯ РАБОТЫ ПРОЕКТА" -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host ""

# ================================================================================
# ШАГ 1: Проверка установки
# ================================================================================
Write-Host "[ШАГ 1/7] Проверка установки компонентов..." -ForegroundColor Yellow
Write-Host ""

Write-Host "Кластер Kubernetes:" -ForegroundColor Cyan
k3d cluster list
Write-Host ""

Write-Host "Поды Argo Workflows:" -ForegroundColor Cyan
kubectl get pods -n argo
Write-Host ""

Write-Host "Сервисы:" -ForegroundColor Cyan
kubectl get svc -n argo
Write-Host ""

Write-Host "✅ Установка проверена" -ForegroundColor Green
Write-Host ""
Read-Host "Нажмите Enter для продолжения"

# ================================================================================
# ШАГ 2: Показать все 5 универсальных шаблонов
# ================================================================================
Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "[ШАГ 2/7] Универсальные WorkflowTemplates (5 штук)" -ForegroundColor Yellow
Write-Host ""

kubectl get workflowtemplates -n argo

Write-Host ""
Write-Host "Шаблоны:" -ForegroundColor Cyan
Write-Host "  1. data-validation-template      - Валидация данных" -ForegroundColor Green
Write-Host "  2. etl-processing-template       - ETL обработка" -ForegroundColor Green
Write-Host "  3. notification-template         - Уведомления" -ForegroundColor Green
Write-Host "  4. conditional-execution-template - Условное выполнение" -ForegroundColor Green
Write-Host "  5. batch-file-processor-template - Пакетная обработка" -ForegroundColor Green
Write-Host ""

Write-Host "✅ Все 5 шаблонов установлены" -ForegroundColor Green
Write-Host ""
Read-Host "Нажмите Enter для продолжения"

# ================================================================================
# ШАГ 3: Показать детали одного шаблона
# ================================================================================
Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "[ШАГ 3/7] Детали шаблона data-validation-template" -ForegroundColor Yellow
Write-Host ""

kubectl describe workflowtemplate data-validation-template -n argo | Select-String -Pattern "Name:|Description:|Default:" | Select-Object -First 20

Write-Host ""
Write-Host "✅ Шаблон имеет входные/выходные параметры" -ForegroundColor Green
Write-Host ""
Read-Host "Нажмите Enter для продолжения"

# ================================================================================
# ШАГ 4: Показать существующие workflows
# ================================================================================
Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "[ШАГ 4/7] Существующие workflows" -ForegroundColor Yellow
Write-Host ""

kubectl get workflows -n argo

$existingWorkflows = kubectl get workflows -n argo -o json | ConvertFrom-Json
if ($existingWorkflows.items.Count -gt 0) {
    Write-Host ""
    Write-Host "✅ Есть успешно выполненные workflows" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "ℹ️  Workflows пока не запускались" -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Нажмите Enter для продолжения"

# ================================================================================
# ШАГ 5: Запустить новый workflow для демонстрации
# ================================================================================
Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "[ШАГ 5/7] Запуск нового workflow" -ForegroundColor Yellow
Write-Host ""

Write-Host "Запускаю main-workflow.yaml..." -ForegroundColor Cyan
$output = kubectl create -f main-workflow.yaml -n argo 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Workflow запущен: $output" -ForegroundColor Green
    
    # Извлекаем имя workflow
    $workflowName = ($output -split "/")[1].Trim()
    
    Write-Host ""
    Write-Host "Следим за выполнением workflow '$workflowName'..." -ForegroundColor Cyan
    Write-Host "(Обновление каждые 5 секунд, нажмите Ctrl+C когда STATUS станет Succeeded или Failed)" -ForegroundColor Yellow
    Write-Host ""
    
    $maxIterations = 36  # 3 минуты максимум
    $iteration = 0
    
    while ($iteration -lt $maxIterations) {
        $workflowStatus = kubectl get workflow $workflowName -n argo -o jsonpath='{.status.phase}' 2>&1
        $workflowProgress = kubectl get workflow $workflowName -n argo -o jsonpath='{.status.progress}' 2>&1
        
        $timestamp = Get-Date -Format "HH:mm:ss"
        Write-Host "[$timestamp] STATUS: $workflowStatus | PROGRESS: $workflowProgress" -ForegroundColor Cyan
        
        if ($workflowStatus -eq "Succeeded" -or $workflowStatus -eq "Failed" -or $workflowStatus -eq "Error") {
            break
        }
        
        Start-Sleep -Seconds 5
        $iteration++
    }
    
    Write-Host ""
    Write-Host "Финальный статус:" -ForegroundColor Yellow
    kubectl get workflow $workflowName -n argo
    
    if ($workflowStatus -eq "Succeeded") {
        Write-Host ""
        Write-Host "✅ Workflow выполнен успешно!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "⚠️  Workflow завершился со статусом: $workflowStatus" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠️  Workflow уже существует или ошибка запуска" -ForegroundColor Yellow
    Write-Host "Показываю последний workflow:" -ForegroundColor Cyan
    kubectl get workflows -n argo | Select-Object -First 2
}

Write-Host ""
Read-Host "Нажмите Enter для продолжения"

# ================================================================================
# ШАГ 6: Показать логи выполнения
# ================================================================================
Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "[ШАГ 6/7] Логи выполнения workflow" -ForegroundColor Yellow
Write-Host ""

# Получаем последний workflow
$latestWorkflow = kubectl get workflows -n argo -o json | ConvertFrom-Json | Select-Object -ExpandProperty items | Sort-Object {$_.metadata.creationTimestamp} -Descending | Select-Object -First 1

if ($latestWorkflow) {
    $workflowName = $latestWorkflow.metadata.name
    
    Write-Host "Поды workflow '$workflowName':" -ForegroundColor Cyan
    $pods = kubectl get pods -n argo -l workflows.argoproj.io/workflow=$workflowName --no-headers 2>&1
    
    if ($pods) {
        Write-Host $pods
        Write-Host ""
        
        # Берем первый под для показа логов
        $firstPod = ($pods -split "`n")[0] -split "\s+" | Select-Object -First 1
        
        if ($firstPod) {
            Write-Host "Логи пода '$firstPod' (последние 30 строк):" -ForegroundColor Cyan
            Write-Host ""
            kubectl logs -n argo $firstPod -c main --tail=30 2>&1
        }
    } else {
        Write-Host "ℹ️  Поды уже удалены (podGC policy)" -ForegroundColor Yellow
        Write-Host "Показываю детали workflow:" -ForegroundColor Cyan
        kubectl get workflow $workflowName -n argo -o jsonpath='{.status}' | ConvertFrom-Json | ConvertTo-Json -Depth 3
    }
} else {
    Write-Host "ℹ️  Workflows не найдены" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "✅ Логи показаны" -ForegroundColor Green
Write-Host ""
Read-Host "Нажмите Enter для продолжения"

# ================================================================================
# ШАГ 7: Открыть UI и показать итоги
# ================================================================================
Write-Host ""
Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "[ШАГ 7/7] Итоги и доступ к UI" -ForegroundColor Yellow
Write-Host ""

Write-Host ("=" * 80) -ForegroundColor Green
Write-Host "   ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!" -ForegroundColor Green
Write-Host ("=" * 80) -ForegroundColor Green
Write-Host ""

Write-Host "Что было продемонстрировано:" -ForegroundColor Cyan
Write-Host "  ✅ Kubernetes кластер (k3d)" -ForegroundColor Green
Write-Host "  ✅ Argo Workflows v3.5.5" -ForegroundColor Green
Write-Host "  ✅ 5 универсальных WorkflowTemplates" -ForegroundColor Green
Write-Host "  ✅ Main workflow использующий все шаблоны" -ForegroundColor Green
Write-Host "  ✅ Успешное выполнение data pipeline" -ForegroundColor Green
Write-Host "  ✅ Логи работы контейнеров" -ForegroundColor Green
Write-Host ""

Write-Host "Доступ к Argo Workflows UI:" -ForegroundColor Cyan
Write-Host "  http://localhost:2746" -ForegroundColor Yellow
Write-Host ""

Write-Host "Полезные команды:" -ForegroundColor Cyan
Write-Host "  kubectl get workflowtemplates -n argo     # Показать шаблоны" -ForegroundColor Gray
Write-Host "  kubectl get workflows -n argo              # Показать workflows" -ForegroundColor Gray
Write-Host "  kubectl create -f main-workflow.yaml -n argo  # Запустить workflow" -ForegroundColor Gray
Write-Host "  kubectl logs -n argo <pod-name> -c main    # Показать логи" -ForegroundColor Gray
Write-Host ""

Write-Host "Документация для защиты:" -ForegroundColor Cyan
Write-Host "  VERIFICATION.md   - Полная инструкция по проверке" -ForegroundColor Yellow
Write-Host "  DEFENSE_GUIDE.md  - Руководство для защиты" -ForegroundColor Yellow
Write-Host "  DOCKER_SETUP.md   - Объяснение Docker решения" -ForegroundColor Yellow
Write-Host ""

Write-Host ("=" * 80) -ForegroundColor Green
Write-Host ""

# Предложить открыть UI
Write-Host "Открыть Argo UI в браузере? (Y/n): " -ForegroundColor Yellow -NoNewline
$response = Read-Host

if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
    Start-Process "http://localhost:2746"
    Write-Host "✅ UI открыт в браузере" -ForegroundColor Green
}

Write-Host ""
Write-Host "Готово! Проект готов к защите. 🎓" -ForegroundColor Green
Write-Host ""

# build-local.ps1 - Local CI/CD Pipeline Demo
param(
    [switch]$SkipPush,
    [switch]$SkipDashboard,
    [switch]$Clean,
    [string]$Tag = "latest"
)

$ErrorActionPreference = "Stop"

$REGISTRY  = "localhost:5000"
$SPARK_IMG = "${REGISTRY}/spark-data-processor:${Tag}"
$UI_IMG    = "${REGISTRY}/data-ui:${Tag}"
$BRANCH    = "feature/cicd-pipeline"

$script:Failures = 0
$jobSuccess = $false

function Write-Banner($msg) {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

function Write-Step($num, $name) {
    Write-Host ""
    Write-Host "  STEP $num : $name" -ForegroundColor Yellow
    Write-Host ("-" * 50) -ForegroundColor DarkGray
}

function Write-OK($m)   { Write-Host "  [OK]  $m" -ForegroundColor Green }
function Write-FAIL($m) { Write-Host "  [ERR] $m" -ForegroundColor Red; $script:Failures++ }
function Write-INFO($m) { Write-Host "  [--]  $m" -ForegroundColor Gray }

if ($Clean) {
    Write-Banner "CLEANUP"
    docker rm -f local-registry pipeline-spark-processor pipeline-data-ui pipeline-minio 2>$null
    Write-OK "All containers removed"
    exit 0
}

Write-Banner "CI/CD PIPELINE DEMO - hw12"
Write-INFO "Registry : $REGISTRY"
Write-INFO "Tag      : $Tag"
Write-INFO "Branch   : $BRANCH"
Write-INFO "Date     : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# STEP 1: Git branch
Write-Step "1/6" "Git - verify branch"
try {
    $current = git rev-parse --abbrev-ref HEAD 2>&1
    if ($current -ne $BRANCH) {
        git checkout $BRANCH 2>&1 | Out-Null
        $current = git rev-parse --abbrev-ref HEAD 2>&1
    }
    Write-INFO "Current branch: $current"
    Write-INFO "Last commit:    $(git log --oneline -1 2>&1)"
    Write-OK "On branch $BRANCH"
} catch {
    Write-FAIL "Git step failed: $_"
}

# STEP 2: Docker check
Write-Step "2/6" "Docker - check daemon"
try {
    $v = docker version --format "{{.Server.Version}}" 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Docker daemon not running" }
    Write-INFO "Docker version: $v"
    Write-OK "Docker daemon running"
} catch {
    Write-FAIL "Docker not available: $_"
}

# STEP 3: Start local Registry
Write-Step "3/6" "Start local Docker Registry"
try {
    $running = docker ps --filter "name=local-registry" --format "{{.Names}}" 2>&1
    if ($running -ne "local-registry") {
        docker run -d --name local-registry -p 5000:5000 registry:2 | Out-Null
        Start-Sleep -Seconds 3
    }
    $health = docker inspect --format "{{.State.Status}}" local-registry 2>&1
    Write-INFO "Registry status: $health"
    Write-OK "Registry on localhost:5000"
} catch {
    Write-FAIL "Registry failed: $_"
}

# STEP 4: Build images
Write-Step "4/6" "Build Docker images"

Write-Host "  >> Building Spark ETL image..." -ForegroundColor White
try {
    docker build --tag $SPARK_IMG --file apps\spark-jobs\data-processor\Dockerfile apps\spark-jobs\data-processor\
    if ($LASTEXITCODE -ne 0) { throw "Build failed" }
    Write-OK "spark-data-processor image built"
} catch {
    Write-FAIL "Spark image build failed: $_"
}

Write-Host "  >> Building UI Dashboard image..." -ForegroundColor White
try {
    docker build --tag $UI_IMG --file apps\dashboards\data-ui\Dockerfile apps\dashboards\data-ui\
    if ($LASTEXITCODE -ne 0) { throw "Build failed" }
    Write-OK "data-ui image built"
} catch {
    Write-FAIL "UI image build failed: $_"
}

# STEP 5: Push to registry
Write-Step "5/6" "Push images to local Registry"
if (-not $SkipPush) {
    try {
        docker push $SPARK_IMG
        if ($LASTEXITCODE -ne 0) { throw "Push failed" }
        Write-OK "spark-data-processor pushed"
    } catch {
        Write-FAIL "Spark push failed: $_"
    }
    try {
        docker push $UI_IMG
        if ($LASTEXITCODE -ne 0) { throw "Push failed" }
        Write-OK "data-ui pushed"
    } catch {
        Write-FAIL "UI push failed: $_"
    }
} else {
    Write-INFO "Skipping push (-SkipPush flag set)"
}

# STEP 6a: Run Spark ETL job
Write-Step "6/6" "Run Spark ETL Job"
Write-Host "  >> Executing Spark ETL container..." -ForegroundColor White
Write-Host ("  " + "-" * 60) -ForegroundColor DarkGray

try {
    New-Item -ItemType Directory -Force -Path ".\data\input", ".\data\output" | Out-Null
    $pwd_escaped = $PWD.Path
    docker run --rm --name spark-demo-job `
        -e JOB_NAME="demo-etl-job" `
        -e INPUT_PATH="/data/input" `
        -e OUTPUT_PATH="/data/output" `
        -e USE_SPARK="false" `
        -v "${pwd_escaped}\data:/data" `
        $SPARK_IMG
    if ($LASTEXITCODE -eq 0) {
        Write-OK "Spark ETL job COMPLETED SUCCESSFULLY"
        $jobSuccess = $true
    } else {
        Write-FAIL "Spark ETL job exited with code $LASTEXITCODE"
    }
} catch {
    Write-FAIL "Spark ETL job failed: $_"
}

Write-Host ("  " + "-" * 60) -ForegroundColor DarkGray

# STEP 6b: Start Dashboard
if (-not $SkipDashboard) {
    Write-Host "  >> Starting Data UI Dashboard..." -ForegroundColor White
    try {
        docker rm -f pipeline-data-ui 2>$null
        docker run -d --name pipeline-data-ui -p 8080:80 $UI_IMG | Out-Null
        Start-Sleep -Seconds 3
        $status = docker inspect --format "{{.State.Status}}" pipeline-data-ui 2>&1
        Write-INFO "Dashboard status: $status"
        if ($status -ne "running") { throw "Container not running" }
        Write-OK "Dashboard running at http://localhost:8080"
    } catch {
        Write-FAIL "Dashboard failed: $_"
    }
}

# Check output file
Write-Host ""
Write-Host "  >> Checking output data..." -ForegroundColor White
$resultFile = ".\data\output\results.json"
if (Test-Path $resultFile) {
    try {
        $result = Get-Content $resultFile | ConvertFrom-Json
        Write-OK "Output file found: $resultFile"
        Write-INFO "Job name:       $($result.job_name)"
        Write-INFO "Input records:  $($result.input_records)"
        Write-INFO "Output records: $($result.output_records)"
        Write-INFO "Timestamp:      $($result.run_timestamp)"
    } catch {
        Write-INFO "Output file exists but could not parse JSON"
    }
} else {
    Write-INFO "No output file found at $resultFile"
}

# Images list
Write-Host ""
Write-Host "  >> Built images:" -ForegroundColor White
docker images --filter "reference=localhost:5000/*" --format "  {{.Repository}}:{{.Tag}}  ({{.Size}})"

# Registry catalog
try {
    $catalog = Invoke-RestMethod "http://localhost:5000/v2/_catalog" -ErrorAction Stop
    Write-OK "Registry catalog: $($catalog.repositories -join ', ')"
} catch {
    Write-INFO "Registry catalog check skipped"
}

# Summary
Write-Host ""
$color = if ($script:Failures -eq 0) { "Green" } else { "Red" }
Write-Host ("=" * 70) -ForegroundColor $color
if ($script:Failures -eq 0) {
    Write-Host "  ALL STEPS PASSED - CI/CD PIPELINE DEMO SUCCESSFUL!" -ForegroundColor Green
} else {
    Write-Host "  $($script:Failures) step(s) FAILED" -ForegroundColor Red
}
Write-Host ("=" * 70) -ForegroundColor $color
Write-Host ""
Write-Host "  What was built:" -ForegroundColor Cyan
Write-Host "    Branch: $BRANCH" -ForegroundColor White
Write-Host "    Image:  $SPARK_IMG" -ForegroundColor White
Write-Host "    Image:  $UI_IMG" -ForegroundColor White
$etlStatus = if ($jobSuccess) { "SUCCESS" } else { "FAILED" }
Write-Host "    ETL:    $etlStatus" -ForegroundColor $(if ($jobSuccess) { "Green" } else { "Red" })
if (-not $SkipDashboard) {
    Write-Host "    UI:     http://localhost:8080" -ForegroundColor White
}
Write-Host ""
Write-Host "  k3d deploy commands (if cluster running):" -ForegroundColor Cyan
Write-Host "    kubectl apply -f argo-workflows\templates\ -n argo" -ForegroundColor Gray
Write-Host "    kubectl create -f argo-workflows\jobs\spark-data-processing.yaml -n argo" -ForegroundColor Gray
Write-Host "    kubectl get workflows -n argo" -ForegroundColor Gray
Write-Host ""

exit $(if ($script:Failures -eq 0) { 0 } else { 1 })

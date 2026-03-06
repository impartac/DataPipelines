# PowerShell script to run Spark benchmarks in Docker

param(
    [string]$Size = "small"
)

Write-Host "==========================================" -ForegroundColor Green
Write-Host "Spark Performance Benchmark - Docker Runner" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""

# Create reports directory if it doesn't exist
if (-not (Test-Path "reports")) {
    New-Item -ItemType Directory -Path "reports" | Out-Null
    Write-Host "Created reports directory" -ForegroundColor Yellow
}

switch ($Size.ToLower()) {
    "small" {
        Write-Host "Running SMALL benchmark (10,000 rows)..." -ForegroundColor Cyan
        docker-compose up spark-benchmark
    }
    "medium" {
        Write-Host "Running MEDIUM benchmark (100,000 rows)..." -ForegroundColor Cyan
        docker-compose --profile medium up spark-benchmark-medium
    }
    "large" {
        Write-Host "Running LARGE benchmark (1,000,000 rows)..." -ForegroundColor Cyan
        docker-compose --profile large up spark-benchmark-large
    }
    default {
        Write-Host "Invalid size: $Size" -ForegroundColor Red
        Write-Host "Usage: .\run_docker.ps1 [small|medium|large]" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Benchmark completed!" -ForegroundColor Green
Write-Host "Check ./reports/ directory for results" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Green

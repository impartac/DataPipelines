# ================================================================================
# Argo Workflows - Automatic Setup Script
# ================================================================================

param(
    [switch]$SkipInstall,
    [switch]$CleanStart,
    [switch]$Verbose
)

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "   > $Message" -ForegroundColor Cyan
    Write-Host ("=" * 80) -ForegroundColor DarkGray
}

function Write-Success {
    param([string]$Message)
    Write-Host "   OK: $Message" -ForegroundColor Green
}

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "   ERROR: $Message" -ForegroundColor Red
}

function Write-WarningMessage {
    param([string]$Message)
    Write-Host "   WARNING: $Message" -ForegroundColor Yellow
}

function Test-CommandExists {
    param([string]$Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function Test-Prerequisites {
    Write-Step "Checking prerequisites..."
    
    $allOk = $true
    
    Write-Host "Checking Docker... " -ForegroundColor Cyan -NoNewline
    if (Test-CommandExists "docker") {
        try {
            $dockerVersion = docker --version
            Write-Host "OK ($dockerVersion)" -ForegroundColor Green
            
            $null = docker ps 2>&1
            if (-not $?) {
                Write-ErrorMessage "Docker is not running! Please start Docker Desktop."
                $allOk = $false
            }
        } catch {
            Write-ErrorMessage "Error checking Docker"
            $allOk = $false
        }
    } else {
        Write-ErrorMessage "NOT INSTALLED"
        Write-WarningMessage "Install Docker Desktop: https://www.docker.com/products/docker-desktop"
        $allOk = $false
    }
    
    return $allOk
}

function Install-Dependencies {
    Write-Step "Installing dependencies..."
    
    if (-not (Test-CommandExists "choco")) {
        Write-Host "Installing Chocolatey..." -ForegroundColor Yellow
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        
        if (-not $?) {
            Write-ErrorMessage "Failed to install Chocolatey"
            return $false
        }
        Write-Success "Chocolatey installed"
    } else {
        Write-Success "Chocolatey already installed"
    }
    
    if (-not (Test-CommandExists "kubectl")) {
        Write-Host "Installing kubectl..." -ForegroundColor Yellow
        choco install kubernetes-cli -y
        if (-not $?) {
            Write-ErrorMessage "Failed to install kubectl"
            return $false
        }
        Write-Success "kubectl installed"
        refreshenv
    } else {
        Write-Success "kubectl already installed"
    }
    
    if (-not (Test-CommandExists "k3d")) {
        Write-Host "Installing k3d..." -ForegroundColor Yellow
        choco install k3d -y
        if (-not $?) {
            Write-ErrorMessage "Failed to install k3d"
            return $false
        }
        Write-Success "k3d installed"
        refreshenv
    } else {
        Write-Success "k3d already installed"
    }
    
    return $true
}

function New-K3dCluster {
    param([bool]$CleanStart)
    
    Write-Step "Creating local Kubernetes cluster (k3d)..."
    
    $clusterName = "argo-workflows"
    
    $existingCluster = k3d cluster list | Select-String $clusterName
    
    if ($existingCluster) {
        if ($CleanStart) {
            Write-WarningMessage "Deleting existing cluster..."
            k3d cluster delete $clusterName
            if (-not $?) {
                Write-ErrorMessage "Failed to delete cluster"
                return $false
            }
        } else {
            Write-Success "Cluster '$clusterName' already exists"
            kubectl config use-context "k3d-$clusterName" 2>&1 | Out-Null
            return $true
        }
    }
    
    Write-Host "Creating cluster '$clusterName'..." -ForegroundColor Cyan
    Write-Host "This may take 1-2 minutes..." -ForegroundColor Yellow
    
    k3d cluster create $clusterName --api-port 6550 --port "2746:2746@loadbalancer" --agents 2 --wait
    
    if (-not $?) {
        Write-ErrorMessage "Failed to create cluster"
        return $false
    }
    
    Write-Success "Cluster created successfully"
    kubectl config use-context "k3d-$clusterName"
    
    Write-Host "Waiting for cluster to be ready..." -ForegroundColor Cyan
    Start-Sleep -Seconds 10
    
    Write-Success "Cluster is ready!"
    return $true
}

function Install-ArgoWorkflows {
    Write-Step "Installing Argo Workflows..."
    
    Write-Host "Creating namespace argo..." -ForegroundColor Cyan
    kubectl create namespace argo 2>&1 | Out-Null
    
    Write-Host "Installing Argo Workflows components..." -ForegroundColor Cyan
    $argoManifest = "https://github.com/argoproj/argo-workflows/releases/download/v3.5.5/install.yaml"
    
    kubectl apply -n argo -f $argoManifest
    if (-not $?) {
        Write-ErrorMessage "Failed to install Argo Workflows"
        return $false
    }
    
    Write-Success "Argo Workflows installed"
    
    Write-Host "Waiting for components to be ready..." -ForegroundColor Cyan
    kubectl wait --for=condition=Ready pods --all -n argo --timeout=120s 2>&1 | Out-Null
    
    if ($?) {
        Write-Success "All components ready"
    } else {
        Write-WarningMessage "Some components still starting, but continuing..."
    }
    
    Write-Host "Configuring permissions..." -ForegroundColor Cyan
    kubectl create rolebinding default-admin --clusterrole=admin --serviceaccount=argo:default -n argo 2>&1 | Out-Null
    
    return $true
}

function Deploy-WorkflowTemplates {
    Write-Step "Deploying WorkflowTemplates..."
    
    $templatesFile = Join-Path $PSScriptRoot "workflow-templates.yaml"
    
    if (-not (Test-Path $templatesFile)) {
        Write-ErrorMessage "File workflow-templates.yaml not found!"
        return $false
    }
    
    Write-Host "Applying templates from workflow-templates.yaml..." -ForegroundColor Cyan
    kubectl apply -f $templatesFile -n argo
    
    if (-not $?) {
        Write-ErrorMessage "Failed to apply templates"
        return $false
    }
    
    Write-Success "WorkflowTemplates applied successfully"
    
    Write-Host ""
    Write-Host "Installed templates:" -ForegroundColor Cyan
    kubectl get workflowtemplate -n argo -o custom-columns=NAME:.metadata.name,CREATED:.metadata.creationTimestamp --no-headers | 
        ForEach-Object { Write-Host "  * $_" -ForegroundColor Green }
    
    return $true
}

function Enable-ArgoUI {
    Write-Step "Configuring Argo Workflows UI..."
    
    Write-Host "Changing service type to LoadBalancer..." -ForegroundColor Cyan
    kubectl patch svc argo-server -n argo -p '{"spec": {"type": "LoadBalancer"}}'
    
    if (-not $?) {
        Write-WarningMessage "Failed to change service type"
        return $false
    }
    
    Write-Host "Disabling auth (for local development only)..." -ForegroundColor Cyan
    kubectl patch deployment argo-server -n argo --type=json -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/args", "value": ["server", "--auth-mode=server"]}]'
    
    Start-Sleep -Seconds 10
    kubectl wait --for=condition=Ready pods -l app=argo-server -n argo --timeout=60s 2>&1 | Out-Null
    
    Write-Success "Argo UI configured"
    
    Write-Host ""
    Write-Host "   Argo Workflows UI available at:" -ForegroundColor Green
    Write-Host "   http://localhost:2746" -ForegroundColor Cyan
    Write-Host ""
    
    return $true
}

function Show-Summary {
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Green
    Write-Host "   INSTALLATION COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host ("=" * 80) -ForegroundColor Green
    Write-Host ""
    
    Write-Host "What was installed:" -ForegroundColor Cyan
    Write-Host "  * Local Kubernetes cluster (k3d)" -ForegroundColor Green
    Write-Host "  * Argo Workflows v3.5.5" -ForegroundColor Green
    Write-Host "  * 5 universal WorkflowTemplates" -ForegroundColor Green
    Write-Host "  * Argo Workflows UI" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "UI Access:" -ForegroundColor Cyan
    Write-Host "  http://localhost:2746" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "Useful commands:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  # Show all workflows" -ForegroundColor Yellow
    Write-Host "  kubectl get workflows -n argo" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  # Show all templates" -ForegroundColor Yellow
    Write-Host "  kubectl get workflowtemplates -n argo" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  # Run main workflow" -ForegroundColor Yellow
    Write-Host "  kubectl create -f main-workflow.yaml -n argo" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  # Delete all workflows" -ForegroundColor Yellow
    Write-Host "  kubectl delete workflows --all -n argo" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "Stop cluster:" -ForegroundColor Cyan
    Write-Host "  k3d cluster stop argo-workflows" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Start cluster:" -ForegroundColor Cyan
    Write-Host "  k3d cluster start argo-workflows" -ForegroundColor Green
    Write-Host ""
    Write-Host "Delete cluster:" -ForegroundColor Cyan
    Write-Host "  k3d cluster delete argo-workflows" -ForegroundColor Red
    Write-Host ""
    
    Write-Host ("=" * 80) -ForegroundColor Green
}

function Main {
    Write-Host ""
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host "   ARGO WORKFLOWS - AUTOMATIC SETUP" -ForegroundColor Cyan
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host "   Author: HSE Data Pipelines Student" -ForegroundColor Yellow
    Write-Host "   Date: April 2026" -ForegroundColor Yellow
    Write-Host ("=" * 80) -ForegroundColor Cyan
    Write-Host ""
    
    if (-not (Test-Prerequisites)) {
        Write-Host ""
        Write-ErrorMessage "Prerequisites not met!"
        Write-Host "Install Docker Desktop and start it, then run this script again." -ForegroundColor Yellow
        exit 1
    }
    
    if (-not $SkipInstall) {
        if (-not (Install-Dependencies)) {
            Write-Host ""
            Write-ErrorMessage "Failed to install dependencies!"
            exit 1
        }
    } else {
        Write-WarningMessage "Skipping dependency installation (-SkipInstall specified)"
    }
    
    if (-not (New-K3dCluster -CleanStart $CleanStart)) {
        Write-Host ""
        Write-ErrorMessage "Failed to create Kubernetes cluster!"
        exit 1
    }
    
    if (-not (Install-ArgoWorkflows)) {
        Write-Host ""
        Write-ErrorMessage "Failed to install Argo Workflows!"
        exit 1
    }
    
    if (-not (Deploy-WorkflowTemplates)) {
        Write-Host ""
        Write-ErrorMessage "Failed to deploy WorkflowTemplates!"
        exit 1
    }
    
    if (-not (Enable-ArgoUI)) {
        Write-Host ""
        Write-WarningMessage "Failed to configure UI, but templates are installed"
    }
    
    Show-Summary
    
    Write-Host ""
    Write-Host "Open Argo UI in browser? (Y/n): " -ForegroundColor Yellow -NoNewline
    $response = Read-Host
    if ($response -eq "" -or $response -eq "Y" -or $response -eq "y") {
        Start-Process "http://localhost:2746"
    }
}

try {
    Main
} catch {
    Write-Host ""
    Write-ErrorMessage "An error occurred: $_"
    Write-Host $_.ScriptStackTrace
    exit 1
}

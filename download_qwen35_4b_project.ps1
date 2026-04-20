param(
    [string]$ProjectRoot = "C:\Users\USER\Documents\SLIIT Lectures & Tutorials\Y4S2\CTSE\Assignment_02",
    [string]$ModelName = "qwen3.5:4b",
    [int]$RetryDelaySeconds = 20
)

$ErrorActionPreference = "Stop"

$ModelsDir = Join-Path $ProjectRoot "ollama_models"
$LogDir = Join-Path $ProjectRoot "logs"
$LogFile = Join-Path $LogDir "ollama_pull.log"

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

function Ensure-Dir {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Test-OllamaInstalled {
    try {
        ollama --version | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Test-OllamaServer {
    try {
        $null = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3
        return $true
    } catch {
        return $false
    }
}

Ensure-Dir $ProjectRoot
Ensure-Dir $ModelsDir
Ensure-Dir $LogDir

if (-not (Test-OllamaInstalled)) {
    throw "Ollama is not installed or not in PATH."
}

Write-Log "Project root: $ProjectRoot"
Write-Log "Model storage: $ModelsDir"

# Set model directory for this session
$env:OLLAMA_MODELS = $ModelsDir
Write-Log "Set OLLAMA_MODELS for this session."

if (-not (Test-OllamaServer)) {
    Write-Log "Ollama server not running. Starting ollama serve in a new window..."
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:OLLAMA_MODELS='$ModelsDir'; ollama serve"
    Start-Sleep -Seconds 5
}

if (-not (Test-OllamaServer)) {
    throw "Ollama server did not start. Start it manually in PowerShell with: `$env:OLLAMA_MODELS='$ModelsDir'; ollama serve"
}

Write-Log "Starting pull for $ModelName"
Write-Log "If interrupted, rerun this script. Ollama pull is designed to resume interrupted downloads."

while ($true) {
    try {
        ollama pull $ModelName
        break
    } catch {
        Write-Log "Pull failed: $($_.Exception.Message)"
        Write-Log "Retrying in $RetryDelaySeconds seconds..."
        Start-Sleep -Seconds $RetryDelaySeconds
    }
}

Write-Log "Verifying model exists..."
$models = ollama list
if ($models -match [regex]::Escape($ModelName)) {
    Write-Log "Download complete: $ModelName"
    Write-Log "Stored under: $ModelsDir"
} else {
    throw "Pull finished but model was not found in 'ollama list'."
}
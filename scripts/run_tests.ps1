<#
Runs migrations and test suite.
Usage:
  .\scripts\run_tests.ps1            # run locally using venv
  .\scripts\run_tests.ps1 -Docker   # use docker-compose to run services, migrations and tests
#>

param(
    [switch]$Docker
)

$ErrorActionPreference = 'Stop'

function Write-Info($msg){ Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Err($msg){ Write-Host "[ERROR] $msg" -ForegroundColor Red }

if ($Docker) {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Err "Docker CLI not found. Install Docker or run without -Docker to use local venv."
        exit 1
    }

    Write-Info "Starting Docker services..."
    docker compose up -d

    Write-Info "Waiting for Postgres to become ready (max ~60s)..."
    $max = 30
    $i = 0
    while ($i -lt $max) {
        docker compose exec -T db pg_isready -U proxan > $null 2>&1
        if ($LASTEXITCODE -eq 0) { break }
        Start-Sleep -Seconds 2
        $i++
    }
    if ($i -ge $max) {
        Write-Err "Postgres did not become ready in time. Check 'docker compose logs db'"
        exit 1
    }

    Write-Info "Applying Alembic migrations..."
    docker compose run --rm web alembic upgrade head

    Write-Info "Running tests inside web container..."
    docker compose run --rm web pytest -q
    exit $LASTEXITCODE
}
else {
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Err "Python not found on PATH. Install Python 3.10+ or run with -Docker."
        exit 1
    }

    Write-Info "Setting up local virtual environment (\.venv)..."
    if (-not (Test-Path ".venv")) {
        python -m venv .venv
    }

    $venvPython = Join-Path -Path (Get-Item .\.venv).FullName -ChildPath "Scripts\python.exe"
    if (-not (Test-Path $venvPython)) {
        Write-Err "Virtual env python not found at $venvPython"
        exit 1
    }

    Write-Info "Installing dependencies into venv..."
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r requirements.txt

    if ((Test-Path ".env.example") -and -not (Test-Path ".env")) {
        Write-Info "Copying .env.example to .env"
        Copy-Item .env.example .env
    }

    Write-Info "Running Alembic migrations (ensure a PostgreSQL is running and DATABASE_URL in .env points to it)."
    & $venvPython -m alembic upgrade head

    Write-Info "Running pytest..."
    & $venvPython -m pytest -q
    exit $LASTEXITCODE
}

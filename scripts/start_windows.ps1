param([switch]$Detach)
# PowerShell start helper for Windows
$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $here

if (-Not (Test-Path -Path (Join-Path $here ".." ".env"))) {
    $example = Join-Path $here ".." ".env.example"
    if (Test-Path $example) {
        Copy-Item $example (Join-Path $here ".." ".env")
        Write-Output "Created .env from .env.example (edit with real secrets)."
    }
}

Push-Location (Join-Path $here "..")
if (-Not (Test-Path venv)) {
    python -m venv venv
}
# Activate venv for current session
if (Test-Path .\venv\Scripts\Activate.ps1) {
    . .\venv\Scripts\Activate.ps1
}
pip install --upgrade pip
pip install -r requirements.txt

$log = Join-Path (Get-Location) "streamlit.log"
if ($Detach) {
    Start-Process -FilePath python -ArgumentList "-m streamlit run streamlit_app.py --server.port=8501 --server.headless=true" -RedirectStandardOutput $log -RedirectStandardError $log -WindowStyle Hidden
    Write-Output "Started Streamlit (detached). Logs: $log"
} else {
    python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true 2>&1 | Tee-Object -FilePath $log
}

Pop-Location

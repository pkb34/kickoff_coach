$ErrorActionPreference = 'Stop'
$staffSecret = Read-Host 'Create a password for this local staff session' -AsSecureString
$env:WPTI_STAFF_PASSWORD = [System.Net.NetworkCredential]::new('', $staffSecret).Password
if ([string]::IsNullOrWhiteSpace($env:WPTI_STAFF_PASSWORD)) {
    throw 'A staff password is required.'
}
$env:STUDENT_DB_PATH = Join-Path $PSScriptRoot 'data\submissions.sqlite3'
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    $python = Join-Path $PSScriptRoot '..\..\student_success_agent\.venv\Scripts\python.exe'
}
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Create .venv from requirements.txt first, then run this script again.'
}
Write-Host 'Staff dashboard: http://127.0.0.1:8513/'
& $python -m streamlit run (Join-Path $PSScriptRoot 'staff_dashboard.py') --server.address 127.0.0.1 --server.port 8513 --browser.gatherUsageStats false

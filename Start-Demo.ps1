$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path $python)) { throw 'Create .venv and install .[app] first; see README.md.' }
& $python -c "import gradio, pandas"
if ($LASTEXITCODE -ne 0) { throw 'Install demo dependencies: .venv/Scripts/python.exe -m pip install -e .[app]' }
& $python "$PSScriptRoot/demo/app.py"

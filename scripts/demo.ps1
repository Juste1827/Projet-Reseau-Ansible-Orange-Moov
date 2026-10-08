# WHY : une seule commande pour la démo entretien sur Windows.
# 1) venv Python  2) 10 rendus identiques  3) pytest  4) (optionnel) Docker syntax-check

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "=== 1. Pourquoi un venv : isoler Jinja2/PyYAML du Python systeme ==="
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& .\.venv\Scripts\python.exe -m pip install -q -r requirements.txt

Write-Host "=== 2. Pourquoi 2 rendus d'affilee : prouver l'idempotence (meme SHA256) ==="
& .\.venv\Scripts\python.exe scripts\render_intended.py
& .\.venv\Scripts\python.exe scripts\render_intended.py

Write-Host "=== 3. Pourquoi pytest : un recruteur peut cloner + tester sans te croire sur parole ==="
& .\.venv\Scripts\python.exe -m pytest -q

Write-Host "=== 4. Ansible dans Docker (skip si Docker absent) ==="
if (Get-Command docker -ErrorAction SilentlyContinue) {
    docker build -f docker/Dockerfile -t netauto-ansible-lab .
    docker run --rm -v "${Root}:/work" -w /work netauto-ansible-lab ansible-playbook --syntax-check playbooks/01-deploy-base.yml
} else {
    Write-Host "Docker non trouve : syntax-check Ansible saute (normal sur un PC sans Docker Desktop)."
}

Write-Host "=== Termine. Fichiers a montrer : intended\R1-PE-ABJ.cfg et intended\R2-PE-ABJ.cfg ==="

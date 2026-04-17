param(
    [string]$Idea = "Internal feedback board for developer platform teams",
    [string]$OutputRoot = "runs",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action
    )

    Write-Host ""
    Write-Host "== $Title ==" -ForegroundColor Cyan
    & $Action
}

Invoke-Step -Title "Repository tests" -Action {
    python -m unittest discover -s tests -v
}

if ($SkipBuild) {
    Write-Host ""
    Write-Host "Skipped end-to-end build and generated prototype tests." -ForegroundColor Yellow
    exit 0
}

$summary = $null
Invoke-Step -Title "End-to-end build" -Action {
    $json = python -m multi_agent_builder --idea $Idea --output-root $OutputRoot --json
    $script:summary = $json | ConvertFrom-Json
}

if ($summary.status -ne "success") {
    throw "Build failed with status '$($summary.status)'."
}

$prototypeDir = Join-Path $summary.outputs.run_dir "prototype"
$buildSummary = $summary.outputs.build_summary

Invoke-Step -Title "Generated prototype tests" -Action {
    Push-Location $prototypeDir
    try {
        python -m unittest discover -s tests -v
    }
    finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "All checks passed." -ForegroundColor Green
Write-Host "Run ID: $($summary.run_id)"
Write-Host "Prototype: $prototypeDir"
Write-Host "Build summary: $buildSummary"


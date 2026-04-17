# Test Script for Multi-Agent Builder
# Runs comprehensive verification: repository tests, end-to-end build, and generated prototype tests.
# Ensures the entire pipeline works from idea to working prototype.

param(
    [string]$Idea = "Internal feedback board for developer platform teams",  # Default product idea for testing
    [string]$OutputRoot = "runs",                                             # Directory for build outputs
    [switch]$SkipBuild                                                         # Skip the build step if set
)

# Set error handling to stop on any error
$ErrorActionPreference = "Stop"
# Enable strict mode for better error checking
Set-StrictMode -Version Latest

# Function to run a step with logging
function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title,        # Title of the step for display
        [Parameter(Mandatory = $true)]
        [scriptblock]$Action   # Script block to execute
    )

    Write-Host ""
    Write-Host "== $Title ==" -ForegroundColor Cyan
    & $Action
}

# Run repository unit and integration tests
Invoke-Step -Title "Repository tests" -Action {
    python -m unittest discover -s tests -v
}

# Skip build if requested
if ($SkipBuild) {
    Write-Host ""
    Write-Host "Skipped end-to-end build and generated prototype tests." -ForegroundColor Yellow
    exit 0
}

$summary = $null
# Run end-to-end build with the specified idea
Invoke-Step -Title "End-to-end build" -Action {
    $json = python -m multi_agent_builder --idea $Idea --output-root $OutputRoot --json
    $script:summary = $json | ConvertFrom-Json
}

# Check if build succeeded
if ($summary.status -ne "success") {
    throw "Build failed with status '$($summary.status)'."
}

# Get paths for the generated prototype and build summary
$prototypeDir = Join-Path $summary.outputs.run_dir "prototype"
$buildSummary = $summary.outputs.build_summary

# Run tests on the generated prototype
Invoke-Step -Title "Generated prototype tests" -Action {
    Push-Location $prototypeDir
    try {
        python -m unittest discover -s tests -v
    }
    finally {
        Pop-Location
    }
}

# Report success and key outputs
Write-Host ""
Write-Host "All checks passed." -ForegroundColor Green
Write-Host "Run ID: $($summary.run_id)"
Write-Host "Prototype: $prototypeDir"
Write-Host "Build summary: $buildSummary"


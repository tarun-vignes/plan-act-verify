param(
    [string]$BindHost = "127.0.0.1",
    [int]$Port = 8000,
    [string]$OutputRoot = "runs"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

python -m multi_agent_builder.demo.server --host $BindHost --port $Port --output-root $OutputRoot

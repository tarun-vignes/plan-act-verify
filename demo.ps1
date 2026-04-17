# Demo Script for Multi-Agent Builder
# Launches the browser-based demo UI for the autonomous prototype builder.
# Allows users to submit product ideas and watch live build progress.

param(
    [string]$BindHost = "127.0.0.1",  # Host to bind the server to (default: localhost)
    [int]$Port = 8000,                # Port to run the server on (default: 8000)
    [string]$OutputRoot = "runs"      # Directory to store build outputs (default: runs)
)

# Set error handling to stop on any error
$ErrorActionPreference = "Stop"
# Enable strict mode for better error checking
Set-StrictMode -Version Latest

# Launch the demo server with the specified parameters
python -m multi_agent_builder.demo.server --host $BindHost --port $Port --output-root $OutputRoot

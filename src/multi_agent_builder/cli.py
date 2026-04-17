"""
Command-line interface for the Multi-Agent Prototype Builder.

This module provides the main entry point for running the autonomous build system
from the command line. It accepts a high-level product idea and orchestrates the
entire planning, implementation, testing, and evaluation pipeline.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .orchestration.orchestrator_agent import OrchestratorAgent
from .orchestration.retry import RetryPolicy
from .utils import to_jsonable


def build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Autonomous multi-agent prototype builder")
    parser.add_argument("--idea", required=True, help="High-level product idea to turn into a working prototype")
    parser.add_argument("--output-root", default="runs", help="Directory where build artifacts should be written")
    parser.add_argument("--max-test-retries", type=int, default=2, help="Maximum retries after failed validation")
    parser.add_argument(
        "--max-architecture-retries",
        type=int,
        default=1,
        help="Maximum retries when evaluation requests architecture changes",
    )
    parser.add_argument("--json", action="store_true", help="Emit the final build summary as JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI application.

    Parses arguments, runs the orchestrator, and outputs results.
    Returns 0 on success, 1 on failure.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    # Initialize the orchestrator with retry policies
    orchestrator = OrchestratorAgent(
        output_root=Path(args.output_root),
        retry_policy=RetryPolicy(
            max_test_retries=args.max_test_retries,
            max_architecture_retries=args.max_architecture_retries,
        ),
    )
    # Execute the build pipeline
    result = orchestrator.execute(args.idea)
    if args.json:
        # Output structured JSON for automation
        print(json.dumps(to_jsonable(result.summary), indent=2))
    else:
        # Human-readable output
        print(f"Run ID: {result.run_id}")
        print(f"Prototype entrypoint: {result.implementation.entrypoint}")
        print(f"Tests passed: {result.test_report.passed}")
        print(f"Build summary: {result.run_dir / 'artifacts' / 'build_summary.md'}")
    return 0 if result.summary.status == "success" else 1


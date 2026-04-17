# Multi-Agent Prototype Builder

`multi-agent-builder` is a production-style autonomous build system that turns a high-level product idea into a working Python prototype, generated tests, an evaluation report, and a structured build summary.

The system is intentionally split into independent layers:

- `Orchestrator Agent`: drives milestones, retries, and iteration logs.
- `Specification Agent`: produces a PRD, feature breakdown, user stories, API contracts, assumptions, constraints, and requirement gaps.
- `Architecture Agent`: proposes service boundaries, folder structure, and a persistence-ready schema.
- `Implementation Agent`: generates a working prototype that follows the architecture.
- `Testing Agent`: generates unit and integration tests, runs validation, and returns structured failures.
- `Evaluation Agent`: scores maintainability, highlights quality, security, and scalability risks, and recommends next steps.

The newer production-style extensions in this repo are:

- Parallel implementation workers with explicit file ownership boundaries
- Persistent browser-demo job storage under `runs/_jobs`
- LLM-ready agent backends that let each layer swap deterministic logic for a model-backed implementation later

## Repository Layout

```text
src/multi_agent_builder/
  orchestration/
  planning/
  implementation/
  testing/
  evaluation/
  observability/
tests/
```

The generated application for each run lives under `runs/<timestamp>-<product-slug>/prototype/`.

## Quickstart

1. Run the browser demo locally:

```powershell
.\demo.ps1
```

2. Open `http://127.0.0.1:8000` and submit a product idea.

3. Inspect generated artifacts under `runs/<run-id>/artifacts/`.

## Usage

Run a build from the repository root:

```bash
python -m multi_agent_builder --idea "Internal feedback board for developer platform teams"
```

Run the full local verification flow in one command:

```powershell
.\test.ps1
```

Run the browser demo locally:

```powershell
.\demo.ps1
```

Useful options:

- `.\test.ps1 -SkipBuild`: run only the repository tests.
- `.\test.ps1 -Idea "Inventory tracker for a small operations team"`: test a different product idea end to end.
- `.\demo.ps1 -Port 8010`: launch the showcase UI on a different port.

Useful flags:

- `--output-root runs`: change the artifact destination.
- `--max-test-retries 2`: retry implementation after test failures.
- `--max-architecture-retries 1`: retry the planning layer if evaluation finds architectural issues.
- `--json`: print the final build summary as JSON.

Each run emits:

- `artifacts/requirements.md`
- `artifacts/architecture.md`
- `artifacts/test_results.md`
- `artifacts/evaluation.md`
- `artifacts/build_summary.md`
- `artifacts/build_summary.json`
- `logs/events.jsonl`

## Browser Demo

The repo includes a frontend showcase built on the same orchestration core. It runs product idea builds asynchronously, shows live milestone progress, and lets you open generated artifacts in the browser.

```powershell
python -m multi_agent_builder.demo.server --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000` and submit an idea to see the full planning, implementation, testing, and evaluation pipeline in action.

Browser build jobs are persisted under `runs/_jobs`, so completed runs remain available after restarts.

## Why judges should care

- Demonstrates a full autonomous software engineering pipeline, not only generated ideas.
- Delivers a runnable app, generated tests, and a structured build summary from one prompt.
- Includes a browser UI, Docker deployment path, and CI checks for a polished submission.
- Uses a modular agent architecture so future upgrades can swap in stronger planners, backends, or policy agents.

## CI

GitHub Actions now runs the repository test suite, executes one end-to-end build, and builds plus smoke-tests the demo container:

- [ci.yml](.github/workflows/ci.yml)

## Submission Assets

- [SHOWCASE_COPY.md](SHOWCASE_COPY.md): reusable submission, pitch, and resume copy
- [DEPLOYMENT.md](DEPLOYMENT.md): local, Docker, and generic cloud deployment instructions
- [Dockerfile](Dockerfile): container packaging for the browser demo

## Advanced Architecture Notes

- The implementation layer now uses parallel worker agents under [workers.py](src/multi_agent_builder/implementation/workers.py) so disjoint file slices can scale independently.
- The browser demo persists job state through [job_store.py](src/multi_agent_builder/demo/job_store.py) instead of keeping build state only in memory.
- The planning, architecture, implementation, testing, and evaluation layers all sit behind shared backend interfaces in [agent_backends.py](src/multi_agent_builder/runtime/agent_backends.py), which makes the system ready for future LLM-backed agents without replacing the orchestration contract.

## Design Tradeoffs

- The generated prototype is config-driven instead of free-form code generation. That keeps the system deterministic, testable, and suitable for CI while still producing a working application tailored to the input idea.
- The prototype uses the Python standard library only. That avoids environment drift in a constrained workspace and makes the generated app runnable without installing dependencies.
- The architecture artifact includes a production persistence schema even though the prototype uses an in-memory repository. This keeps the implementation light while preserving a clean path to a database-backed service.

## Scaling To Enterprise Pipelines

This prototype is deliberately small, but the architecture is designed to scale:

1. Replace the heuristic planning layer with LLM-backed planners behind the same agent interfaces.
2. Move orchestration state into a durable store or workflow engine such as Temporal, Prefect, or Dagster so long-running builds survive process restarts.
3. Split implementation into domain-specific workers that own disjoint file trees and execute in parallel under a stronger planner.
4. Add a queue-backed execution fabric so testing, evaluation, security scans, and packaging run as independent jobs with retries and SLAs.
5. Swap the in-memory artifact store for object storage plus structured metadata in Postgres so enterprises can audit every iteration and decision.
6. Introduce policy agents for compliance, dependency governance, secrets handling, and approval gates before deployment.
7. Add multi-repo support so architecture, backend, frontend, infrastructure, and QA streams can evolve independently but still report into one orchestration graph.
8. Feed evaluation outputs into issue trackers and PR automation so the system can open remediation work instead of only reporting technical debt.

In other words, the current implementation behaves like a local vertical slice of an enterprise feature factory: the interfaces are stable, the lifecycle is explicit, and the orchestration loop already exposes the right control points for parallelism, policy, and observability.

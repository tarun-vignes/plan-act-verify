# Deployment Guide

## Local Browser Demo

From the repository root:

```powershell
python -m multi_agent_builder.demo.server --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000`.

The UI now starts builds asynchronously and polls live progress from the backend while the orchestrator runs.
Build-job state is also persisted under `runs/_jobs`, so completed jobs remain available across process restarts.

There is also a Windows helper script:

```powershell
.\demo.ps1
```

## Docker

Build the image:

```bash
docker build -t codex-creator-challenge .
```

Run the container:

```bash
docker run --rm -p 8000:8000 -e PORT=8000 codex-creator-challenge
```

Open `http://127.0.0.1:8000`.

## Generic Cloud Deployment

This app is packaged so it can run on any platform that supports a containerized Python web process.

Startup command:

```bash
python -m multi_agent_builder.demo.server --host 0.0.0.0 --port ${PORT:-8000}
```

Recommended environment variables:

- `PORT`: listener port
- `HOST`: defaults to `127.0.0.1` locally and can be overridden to `0.0.0.0`
- `OUTPUT_ROOT`: where build artifacts are written inside the container or VM

## Notes

- The browser demo uses the same orchestrator as the CLI, so deployment exercises the real autonomous build path.
- Generated artifacts are written to the local filesystem. For a production deployment, back this with persistent disk or object storage.
- Authentication is not implemented. If this is exposed publicly, add auth, request limits, and storage controls first.
- GitHub Actions in [.github/workflows/ci.yml](.github/workflows/ci.yml) validates the Python tests and container startup path on every push or pull request.
- The implementation layer already uses parallel worker agents, which is a good seam for future multi-machine execution if the prototype grows into a larger build pipeline.

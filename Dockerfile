FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000
ENV OUTPUT_ROOT=/app/runs
ENV PYTHONPATH=/app/src

WORKDIR /app

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/runs

COPY pyproject.toml README.md SHOWCASE_COPY.md DEPLOYMENT.md /app/
COPY src /app/src

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os; from urllib.request import urlopen; port = os.getenv('PORT', '8000'); urlopen(f'http://127.0.0.1:{port}/health', timeout=3).read()" || exit 1

CMD ["sh", "-c", "python -m multi_agent_builder.demo.server --host 0.0.0.0 --port ${PORT:-8000} --output-root /app/runs"]

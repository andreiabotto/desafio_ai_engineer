FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt


FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/.cache/huggingface \
    PATH=/install/bin:$PATH \
    PYTHONPATH=/install/lib/python3.11/site-packages:/app/src

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY --from=builder /install /install
COPY pyproject.toml pytest.ini ./
COPY src ./src
COPY data ./data
COPY tests ./tests
COPY scripts ./scripts
COPY examples ./examples
COPY README.md ./

RUN chmod +x /app/scripts/docker-entrypoint.sh \
    && mkdir -p /app/.data /app/.chroma /app/.cache/huggingface \
    && chown -R appuser:appuser /app

USER appuser

VOLUME ["/app/.data", "/app/.chroma", "/app/.cache/huggingface"]

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import emporio_agent; print('ok')" || exit 1

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["chat"]

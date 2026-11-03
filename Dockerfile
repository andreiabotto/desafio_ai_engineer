FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY pyproject.toml pytest.ini ./
COPY src ./src
COPY data ./data
COPY tests ./tests
COPY scripts ./scripts
COPY examples ./examples
COPY README.md ./

RUN pip install -e . && chmod +x /app/scripts/docker-entrypoint.sh

RUN mkdir -p /app/.data /app/.chroma /app/.cache/huggingface

VOLUME ["/app/.data", "/app/.chroma", "/app/.cache/huggingface"]

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
CMD ["chat"]
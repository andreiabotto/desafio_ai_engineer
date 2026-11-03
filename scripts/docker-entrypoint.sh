#!/usr/bin/env bash
set -euo pipefail

cd /app

run_ingest() {
  python - <<'PY'
from emporio_agent.data.ingest_csv import db_ready, ingest_csvs
from emporio_agent.data.ingest_policies import ingest_policies, policies_ready
from emporio_agent.logging_setup import get_logger, setup_logging

setup_logging()
logger = get_logger("emporio_agent.entrypoint")

if not db_ready():
    logger.info("Ingerindo CSVs → SQLite...")
    ingest_csvs()
    logger.info("SQLite pronto")
else:
    logger.info("SQLite já presente")

if not policies_ready():
    logger.info("Indexando políticas (embeddings locais)...")
    ingest_policies()
    logger.info("Índice de políticas pronto")
else:
    logger.info("Índice de políticas já presente")
PY
}

if [[ $# -eq 0 ]]; then
  set -- chat
fi

case "$1" in
  chat)
    run_ingest
    shift
    exec python -m emporio_agent.cli chat "$@"
    ;;
  ui)
    run_ingest
    shift
    exec python -m emporio_agent.cli ui "$@"
    ;;
  ingest)
    shift
    exec python -m emporio_agent.cli ingest "$@"
    ;;
  pytest|test)
    shift
    if [[ "$1" == "pytest" ]]; then
      shift
    fi
    exec pytest "$@"
    ;;
  *)
    exec "$@"
    ;;
esac

#!/usr/bin/env bash
set -euo pipefail

cd /app

run_ingest() {
  python - <<'PY'
from emporio_agent.data.ingest_csv import db_ready, ingest_csvs
from emporio_agent.data.ingest_policies import ingest_policies, policies_ready

if not db_ready():
    print("Ingerindo CSVs → SQLite...")
    ingest_csvs()
else:
    print("SQLite já presente.")

if not policies_ready():
    print("Indexando políticas (embeddings locais)...")
    ingest_policies()
else:
    print("Índice de políticas já presente.")
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

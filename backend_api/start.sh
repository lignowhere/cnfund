#!/bin/sh
set -eu

mkdir -p /app/storage/data /app/storage/exports
ln -sfn /app/storage/data /app/data
ln -sfn /app/storage/exports /app/exports

exec python -m uvicorn backend_api.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

#!/bin/sh
set -eu

alembic -c alembic.ini upgrade head
exec uvicorn fraudlens.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-127.0.0.1}"

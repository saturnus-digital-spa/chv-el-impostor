#!/bin/sh
set -e

if [ "$STAGE" = "PROD" ]; then
  exec gunicorn core.asgi:application \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-5} \
    --timeout ${GUNICORN_TIMEOUT:-30} \
    --worker-class uvicorn.workers.UvicornWorker
else
  python manage.py runserver 0.0.0.0:8000
fi
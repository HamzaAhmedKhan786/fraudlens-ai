FROM python:3.12-slim
WORKDIR /app
COPY apps/api/pyproject.toml .
COPY apps/api/src ./src
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/migrations ./migrations
COPY apps/api/entrypoint.sh ./entrypoint.sh
RUN pip install --no-cache-dir .
RUN chmod +x ./entrypoint.sh
ENV PYTHONPATH=/app/src
EXPOSE 8000
CMD ["./entrypoint.sh"]

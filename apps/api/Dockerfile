FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu \
    tesseract-ocr-spa tesseract-ocr-ita tesseract-ocr-urd \
    tesseract-ocr-fra tesseract-ocr-ara \
    && rm -rf /var/lib/apt/lists/*
COPY apps/api/pyproject.toml .
COPY apps/api/src ./src
COPY apps/api/alembic.ini ./alembic.ini
COPY apps/api/migrations ./migrations
COPY apps/api/entrypoint.sh ./entrypoint.sh
RUN pip install --no-cache-dir .
RUN chmod +x ./entrypoint.sh
ENV PYTHONPATH=/app/src
ENV TESSERACT_CMD=tesseract TESSDATA_PREFIX=/usr/share/tesseract-ocr/5/tessdata
EXPOSE 8000
CMD ["./entrypoint.sh"]

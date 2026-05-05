FROM python:3.13.2-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM python:3.13.2-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

RUN addgroup --gid 1001 --system app && \
    adduser --uid 1001 --system --group --home /home/app --shell /bin/bash app && \
    mkdir -p /home/app/.config/matplotlib && \
    chown -R app:app /home/app

USER app
STOPSIGNAL SIGINT

ENV MPLCONFIGDIR=/home/app/.config/matplotlib \
    SECRET_FOLDER_PATH=/app/secret \
    DATA_FOLDER_PATH=/app/data \
    ASSETS_FOLDER_PATH=/app/assets

COPY . /app
ENTRYPOINT ["python3", "main.py"]

FROM python:3.13.2-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

FROM denoland/deno:bin AS deno

FROM python:3.13.2-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates \
        dnsutils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && \
    rm -rf /wheels

COPY --from=deno /deno /usr/local/bin/deno

#RUN addgroup --gid 1001 --system app && \
#    adduser --no-create-home --shell /bin/false --disabled-password --uid 1001 --system --group app

RUN addgroup --gid 1001 --system app && \
    adduser --uid 1001 --system --group --home /home/app --shell /bin/bash app && \
    mkdir -p /home/app/.config/matplotlib && \
    chown -R app:app /home/app

USER app
STOPSIGNAL SIGINT

ENV MPLCONFIGDIR=/home/app/.config/matplotlib

COPY . /app
ENTRYPOINT ["python3", "main.py"]

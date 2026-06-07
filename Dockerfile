FROM python:3.14.5-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PYTHON_DOWNLOADS=0 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-editable --no-dev

# =====================================================

FROM python:3.14.5-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=builder /app/.venv /app/.venv
COPY ./main.py /app/
COPY ./lib /app/lib
COPY ./assets /app/assets

RUN addgroup --gid 1001 --system app && \
    adduser --uid 1001 --system --group --home /home/app --shell /bin/bash app && \
    mkdir -p /home/app/.config/matplotlib && \
    chown -R app:app /home/app /app

USER app

ENV PATH="/app/.venv/bin:$PATH"

ENV MPLCONFIGDIR=/home/app/.config/matplotlib
ENV SECRET_FOLDER_PATH=/app/secret
ENV DATA_FOLDER_PATH=/app/data
ENV ASSETS_FOLDER_PATH=/app/assets

STOPSIGNAL SIGINT

ENTRYPOINT ["/app/.venv/bin/python", "main.py"]

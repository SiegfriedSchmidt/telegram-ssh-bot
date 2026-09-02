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
# FINAL STAGE
# =====================================================
FROM python:3.14.5-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 1. Create user, group, and config directories FIRST
RUN addgroup --gid 1001 --system app && \
    adduser --uid 1001 --system --group --home /home/app --shell /bin/bash app && \
    mkdir -p /home/app/.config/matplotlib && \
    chown -R app:app /home/app

# 2. Copy files WITH --chown to avoid layer duplication
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app ./main.py /app/
COPY --chown=app:app ./lib /app/lib
COPY --chown=app:app ./assets /app/assets

USER app

ENV PATH="/app/.venv/bin:$PATH"
ENV MPLCONFIGDIR=/home/app/.config/matplotlib
ENV SECRET_FOLDER_PATH=/app/secret
ENV DATA_FOLDER_PATH=/app/data
ENV ASSETS_FOLDER_PATH=/app/assets

STOPSIGNAL SIGINT

ENTRYPOINT ["/app/.venv/bin/python", "main.py"]

FROM bitnami/minideb:bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install -y \
    pandoc \
    curl \
    dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables early
ENV PATH="/home/app_user/venv/bin:$PATH" \
    VIRTUAL_ENV="/home/app_user/venv" \
    UV_PYTHON=3.13 \
    HOME="/home/app_user" \
    PYTHONPATH="/app:."

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml

RUN uv sync --active

ENV UV_PYTHON="/home/app_user/venv/bin/python"

CMD ["bash"]
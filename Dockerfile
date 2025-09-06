FROM bitnami/minideb:bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install -y \
    pandoc \
    curl \
    dos2unix \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables early
ENV PATH="/home/app_user/venv/bin:$PATH" \
    VIRTUAL_ENV="/home/app_user/venv" \
    UV_PYTHON=3.13 \
    HOME="/home/app_user" \
    PYTHONPATH="/app:."

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

RUN uv sync --active

COPY --chmod=0755 *.bsh /app/
COPY *.py /app/

ENV UV_PYTHON="/home/app_user/venv/bin/python"

CMD ["bash"]
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    pandoc \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-nix.txt .

RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    /root/.local/bin/uv pip install --system --no-cache -r requirements-nix.txt

CMD ["bash"]
FROM python:3.11-slim

WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY .env.example .env

# Install Python dependencies
RUN uv pip install --system -e .

CMD ["/bin/bash"]

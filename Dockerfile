# Dockerfile for Education Insights Agent System
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including uv
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy dependency files and README (needed by pyproject.toml)
COPY pyproject.toml .
COPY uv.lock .
COPY README.md .

# Install Python dependencies using uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY agents/ ./agents/
COPY tools/ ./tools/
COPY mcp_servers/ ./mcp_servers/
COPY static/ ./static/
COPY api.py .
COPY main.py .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run the FastAPI application
CMD [".venv/bin/uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080", "--timeout-keep-alive", "300"]


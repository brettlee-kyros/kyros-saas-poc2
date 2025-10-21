FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared-config package (will be mounted as volume)
# RUN pip install -e /app/packages/shared-config

# Copy application source
COPY src/ /app/src/

# Copy tests for pytest
COPY tests/ /app/tests/
COPY pytest.ini /app/pytest.ini

# Expose port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

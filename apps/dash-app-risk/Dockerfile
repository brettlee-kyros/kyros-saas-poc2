FROM python:3.11-slim

WORKDIR /app

# Copy and install Python dependencies first (for caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app.py .
COPY auth_middleware.py .
COPY data_client.py .
COPY error_page.py .

# Install shared-config from local package
# This will be mounted at runtime from the packages/ directory
# For now, create placeholder for import path
RUN mkdir -p /app/packages/shared-config/src

# Expose port
EXPOSE 8051

# Run Dash app
CMD ["python", "app.py"]

FROM python:3.11-slim

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ /app/src/

# Expose port
EXPOSE 8051

# Run Dash app
CMD ["python", "src/app.py"]

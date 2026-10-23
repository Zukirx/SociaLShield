FROM python:3.10-slim

WORKDIR /app

# Install system dependencies if any are needed for ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment path so modules can be imported
ENV PYTHONPATH=/app

# Expose the API port
EXPOSE 8000

# Start the FastAPI application
CMD ["uvicorn", "core.api:app", "--host", "0.0.0.0", "--port", "8000"]

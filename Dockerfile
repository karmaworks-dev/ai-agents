# Use a slim official Python image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Keep python quiet and unbuffered (good for logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy and install dependencies first to benefit from docker cache
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy full repo
COPY . /app

# Create agent_data directories (for logs, data, temp)
RUN mkdir -p /app/agent_data/logs /app/agent_data/data /app/agent_data/temp

# Expose port
EXPOSE 5000

# FIXED: Correct path to trading_app.py (in root, not main/)
CMD ["python", "trading_app.py"]

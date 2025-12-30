# Use the Python version specified in the source documentation
FROM python:3.10-slim

# Install system dependencies
# Added llvm and build-essential for numerical/trading library support
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    llvm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Keep python quiet and unbuffered for real-time dashboard logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy repo (ensure .env is in .dockerignore)
COPY . .

# Create the EXACT directory the code expects for data [3, 4]
RUN mkdir -p /app/src/data

# Expose the dashboard port [6]
EXPOSE 5000

# Entry point for the dashboard backend
CMD ["python", "trading_app.py"]

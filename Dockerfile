# Use the specific Python version used during development [1]
FROM python:3.10-slim

# Install system dependencies
# Fixed: Comments moved outside the RUN command to prevent syntax errors
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    llvm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Optimization: Keep python quiet and unbuffered for real-time dashboard logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Optimization: Install dependencies with no cache to save disk space
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full repository
COPY . .

# Critical: Create the exact directory the code expects for persistent data [2, 3]
# Also create temp_data for agent analysis cycles [4]
RUN mkdir -p /app/src/data /app/temp_data

# Expose the dashboard port (default 5000) [5, 6]
EXPOSE 5000

# Start the dashboard backend
CMD ["python", "trading_app.py"]

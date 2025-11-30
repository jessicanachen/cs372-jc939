# Dockerfile
FROM python:3.11-slim

# Prevent Python from writing .pyc & use unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps (if you need any, otherwise you can skip RUN line)
# RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app ./app

# Expose port (Cloud Run uses PORT env var, but this is nice for local runs)
EXPOSE 8080

# Start FastAPI via uvicorn, listening on PORT (defaults to 8080)
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}


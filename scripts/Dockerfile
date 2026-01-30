# Production Dockerfile
FROM python:3.11-slim

# basic env vars for python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Create non-root user
RUN groupadd -g 1000 dexkeeper && \
    useradd -u 1000 -g dexkeeper -m dexkeeper

WORKDIR /app

# Install dependencies first (caching)
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy bot code (and healthcheck)
COPY dexkeeper_bot.py .
COPY healthcheck.py .

# Permissions
RUN chown -R dexkeeper:dexkeeper /app

# Switch to non-root
USER dexkeeper

# Persistence
VOLUME /app/data

# Command
CMD ["python", "dexkeeper_bot.py"]

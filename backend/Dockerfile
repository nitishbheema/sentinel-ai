FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for compilation & network tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user and group
RUN groupadd -g 1001 sentinel && useradd -u 1001 -g sentinel -s /bin/bash -m sentinel

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY ml-engine/ ./ml-engine/
COPY detection-rules/ ./detection-rules/

# Set ownership to non-root user
RUN chown -R sentinel:sentinel /app

WORKDIR /app/backend

USER sentinel

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

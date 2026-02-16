FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Python dependencies first for better layer caching
COPY backend_api/requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /tmp/requirements.txt

# Copy only backend runtime sources (keep image small for reliable registry push)
COPY backend_api /app/backend_api
COPY core /app/core
COPY utils /app/utils
COPY config.py /app/config.py
COPY helpers.py /app/helpers.py

RUN chmod +x /app/backend_api/start.sh

FROM python:3.10-slim

# Install system deps and ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy project
COPY . /app

# Ensure outputs folder exists
RUN mkdir -p /app/outputs /app/outputs/shorts /app/outputs/thumbnails /app/outputs/tts

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]

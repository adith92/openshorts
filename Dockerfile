# Gemini CLI requires Node.js 20+.
FROM node:22-slim AS gemini-cli
RUN npm install -g @google/gemini-cli@latest

# Multi-stage build for smaller final image
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install FFmpeg, OpenCV, and Node.js runtime dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libstdc++6 \
    libgcc-s1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Python virtual environment.
COPY --from=builder /opt/venv /opt/venv

# Copy Node.js 22 and the official Gemini CLI from the dedicated build stage.
COPY --from=gemini-cli /usr/local/bin/node /usr/local/bin/node
COPY --from=gemini-cli /usr/local/lib/node_modules/@google/gemini-cli /usr/local/lib/node_modules/@google/gemini-cli
RUN ln -s /usr/local/lib/node_modules/@google/gemini-cli/bundle/gemini.js /usr/local/bin/gemini \
    && chmod +x /usr/local/lib/node_modules/@google/gemini-cli/bundle/gemini.js

ENV PATH="/opt/venv/bin:/usr/local/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV HOME=/app
ENV GEMINI_FORCE_ENCRYPTED_FILE_STORAGE=true
ENV NO_BROWSER=true

# Always upgrade yt-dlp to latest (YouTube bot-detection changes frequently).
RUN pip install --upgrade --no-cache-dir yt-dlp

# Copy application code.
COPY . .

# Create a non-root user.
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Create writable application, OAuth, and cache directories.
RUN mkdir -p \
    /app/uploads \
    /app/output \
    /app/.gemini \
    /tmp/Ultralytics \
    /tmp/openshorts-gemini-cli \
    && chown -R appuser:appuser \
        /app \
        /tmp/Ultralytics \
        /tmp/openshorts-gemini-cli

USER appuser

# Pre-download YOLO model on build.
RUN python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

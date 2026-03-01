ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:latest

FROM ${BUILD_FROM}

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    ca-certificates \
    curl \
    bash \
    jq \
    build-base \
    python3-dev \
    openssl-dev \
    libffi-dev

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy API application
COPY api.py .
COPY server.py .
COPY tools.py .
COPY intent.py .
COPY pricing.py .
COPY chat_ui.py .
COPY keywords.json .
COPY config.yaml .
COPY file_upload.py .
COPY rag.py .
COPY memory.py .
COPY chat_bubble.py .
COPY messaging.py .
COPY telegram_bot.py .
COPY whatsapp_bot.py .
COPY fallback.py .
COPY quality_metrics.py .
COPY tool_optimizer.py .
COPY semantic_cache.py .
COPY mcp.py .
COPY mcp_auth.py .
COPY scheduled_tasks.py .
COPY voice_transcription.py .
COPY prompt_caching.py .
COPY image_support.py .
COPY scheduler_agent.py .

# Copy new providers module (v3.17.12+)
COPY providers /app/providers

# Copy rootfs (s6-overlay v3 service structure)
COPY rootfs /

# Make s6 service scripts executable
RUN chmod +x /etc/s6-overlay/s6-rc.d/claude-backend/run \
    && chmod +x /etc/s6-overlay/s6-rc.d/claude-backend/finish

# Expose API port
EXPOSE 5010

# Set environment defaults
ENV DEBUG_MODE=False
ENV ENABLE_FILE_ACCESS=False
ENV API_PORT=5010
ENV HA_URL=http://supervisor/core
ENV TIMEOUT=30
ENV MAX_RETRIES=3

# s6-overlay init system - /init is inherited from base image
# s6 will discover and run /etc/s6-overlay/s6-rc.d/claude-backend/run
ENTRYPOINT ["/init"]

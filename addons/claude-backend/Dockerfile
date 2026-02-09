ARG BUILD_FROM

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

# Copy rootfs (s6-overlay v3 service structure)
COPY rootfs /

# Make s6 service scripts executable
RUN chmod +x /etc/s6-overlay/s6-rc.d/claude-backend/run \
    && chmod +x /etc/s6-overlay/s6-rc.d/claude-backend/finish

# Expose API port
EXPOSE 5000

# Set environment defaults
ENV DEBUG_MODE=False
ENV ENABLE_FILE_ACCESS=False
ENV API_PORT=5000
ENV HA_URL=http://supervisor/core
ENV TIMEOUT=30
ENV MAX_RETRIES=3

# s6-overlay init system - /init is inherited from base image
# s6 will discover and run /etc/s6-overlay/s6-rc.d/claude-backend/run
ENTRYPOINT ["/init"]

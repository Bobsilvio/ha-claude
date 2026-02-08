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

# Create s6-overlay service directory
RUN mkdir -p /etc/services.d/claude-api

# Copy run and finish scripts to services.d for s6-overlay
COPY run.sh /etc/services.d/claude-api/run
COPY finish.sh /etc/services.d/claude-api/finish
RUN chmod +x /etc/services.d/claude-api/run /etc/services.d/claude-api/finish

# Expose API port
EXPOSE 5000

# Set environment defaults
ENV DEBUG_MODE=False
ENV API_PORT=5000
ENV HA_URL=http://homeassistant:8123
ENV TIMEOUT=30
ENV MAX_RETRIES=3

# s6-overlay will run as init through Home Assistant addon init: true setting
CMD ["/bin/bash", "/etc/services.d/claude-api/run"]

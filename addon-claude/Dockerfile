ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install Python and dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    curl

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Copy application
COPY api.py .

# Copy the Claude custom component (will be deployed automatically)
COPY claude_component /app/claude_component

# Copy run script
COPY run.sh /
RUN chmod +x /run.sh

# Expose API port
EXPOSE 5000

# Set environment defaults
ENV DEBUG_MODE=False
ENV API_PORT=5000
ENV HA_URL=http://homeassistant:8123
ENV TIMEOUT=30
ENV MAX_RETRIES=3

CMD [ "/run.sh" ]

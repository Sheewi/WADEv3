# WADE Docker Image
# Multi-stage build for optimized production image

# Build stage
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Set labels
LABEL org.label-schema.build-date=$BUILD_DATE \
      org.label-schema.name="WADE" \
      org.label-schema.description="Weaponized Autonomous Deployment Engine" \
      org.label-schema.url="https://github.com/wade/wade" \
      org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url="https://github.com/wade/wade" \
      org.label-schema.vendor="WADE Team" \
      org.label-schema.version=$VERSION \
      org.label-schema.schema-version="1.0"

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY wade/requirements.txt ./wade/

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r wade/requirements.txt

# Copy source code
COPY . .

# Build the package
RUN cd wade && python -m build

# Install the built package
RUN pip install wade/dist/*.whl

# Production stage
FROM python:3.11-slim as production

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create wade user
RUN groupadd -r wade && useradd -r -g wade -d /opt/wade -s /bin/bash wade

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create necessary directories
RUN mkdir -p /opt/wade /etc/wade /var/log/wade /var/lib/wade /var/run/wade \
    && chown -R wade:wade /opt/wade /var/log/wade /var/lib/wade /var/run/wade \
    && chmod 755 /etc/wade

# Copy application files
COPY --from=builder /app/wade /opt/wade/
COPY --from=builder /app/deploy/docker/entrypoint.sh /opt/wade/
COPY --from=builder /app/deploy/docker/healthcheck.sh /opt/wade/

# Copy configuration templates
COPY --from=builder /app/deploy/config/ /etc/wade/

# Set permissions
RUN chmod +x /opt/wade/entrypoint.sh /opt/wade/healthcheck.sh \
    && chown -R wade:wade /opt/wade

# Switch to wade user
USER wade

# Set work directory
WORKDIR /opt/wade

# Expose ports
EXPOSE 8080 9090

# Set environment variables
ENV WADE_HOME=/opt/wade \
    WADE_CONFIG=/etc/wade/config.json \
    WADE_LOG_LEVEL=INFO \
    WADE_ENV=production \
    PYTHONPATH=/opt/wade \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /opt/wade/healthcheck.sh

# Set entrypoint
ENTRYPOINT ["/opt/wade/entrypoint.sh"]

# Default command
CMD ["wade", "--config", "/etc/wade/config.json"]
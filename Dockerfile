# Use Python 3.12 slim image as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    procps

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY src/ src/
COPY config/ config/
COPY agent_discovery_app.py .

# Create directories for logs and files
RUN mkdir -p logs files

# Set environment variable to use production config
ENV SCANNER_CONFIG_ENV=production

# Expose the UDP and TCP ports
EXPOSE 706/udp 708/tcp

# Health check - check if the main process is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD pgrep -f "python agent_discovery_app.py" > /dev/null || exit 1

# Run the agent discovery app
CMD ["python", "agent_discovery_app.py"]

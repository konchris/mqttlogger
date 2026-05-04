# syntax=docker/dockerfile:1
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Create and set working directory
RUN mkdir /code
WORKDIR /code

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies in a single RUN command to reduce layers
RUN pip install --no-cache-dir --upgrade pip && \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    	libmariadb-dev \
	python3-dev \
	build-essential && \
    pip install --no-cache-dir -r requirements.txt && \
    # Clean up to reduce image size
    apt-get purge -y python3-dev build-essential && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy application code
COPY app.py config.json constants.py ./
COPY mqttlogger ./mqttlogger

# Create a non-root user to run the application
RUN useradd -m appuser
USER appuser

# Run the application
CMD ["python", "app.py"]

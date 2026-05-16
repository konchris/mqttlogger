FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY monitor.py bootstrap_sensors.py ./
# sensors.yml is NOT baked in — mount it as a volume at runtime
CMD ["python", "monitor.py"]

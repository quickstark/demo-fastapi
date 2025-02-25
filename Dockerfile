FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables with updated agent name
ENV PYTHONPATH=/app \
    PORT=8080 \
    DD_ENV="dev" \
    DD_SERVICE="fastapi-app" \
    DD_VERSION="1.0" \
    DD_LOGS_INJECTION=true \
    DD_TRACE_SAMPLE_RATE=1 \
    DD_PROFILING_ENABLED=true \
    DD_DYNAMIC_INSTRUMENTATION_ENABLED=true \
    DD_SYMBOL_DATABASE_UPLOAD_ENABLED=true

# Use python -m to run hypercorn
CMD ["python", "-m", "hypercorn", "main:app", "--bind", "0.0.0.0:8080"]

EXPOSE 8080
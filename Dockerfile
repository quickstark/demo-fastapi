FROM python:3.9-slim

WORKDIR /app

# Install system dependencies and clean up in one layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
    
# Copy application code
COPY . .

# Consolidate all ENV variables into a single layer
ENV PYTHONPATH=/app \
    PORT=8080 \
    DD_ENV="dev" \
    DD_SERVICE="fastapi-app" \
    DD_VERSION="1.0" \
    DD_LOGS_INJECTION=true \
    DD_TRACE_SAMPLE_RATE=1 \
    DD_PROFILING_ENABLED=true \
    DD_DYNAMIC_INSTRUMENTATION_ENABLED=true \
    DD_SYMBOL_DATABASE_UPLOAD_ENABLED=true \
    DD_AGENT_HOST=192.168.1.100 \
    DD_TRACE_AGENT_PORT=8126 \
    DD_DBM_PROPAGATION_MODE=service \
    DD_LLMOBS_ENABLED=true \
    DD_LLMOBS_ML_APP=youtube-summarizer \
    DD_LLMOBS_EVALUATORS="ragas_faithfulness,ragas_context_precision,ragas_answer_relevancy" \
    OPENAI_API_KEY=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 \
    PUID=1026 \
    PGID=100

# Use python -m to run hypercorn
CMD ["python", "-m", "hypercorn", "main:app", "--bind", "0.0.0.0:8080"]

EXPOSE 8080
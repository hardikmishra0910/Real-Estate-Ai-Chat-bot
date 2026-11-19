FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Pre-download the ONNX model at build time so it's in the image
# This avoids downloading 79MB at runtime on the free tier
RUN python -c "from chromadb.utils.embedding_functions import DefaultEmbeddingFunction; ef = DefaultEmbeddingFunction(); r = ef(['test']); print('ONNX model ready, dim=', len(r[0]))"

COPY app/ ./app/

# Pre-scrape and pre-index data into the image so no indexing is needed at runtime
RUN mkdir -p ./data/raw ./data/processed ./data/chromadb
RUN python -c "\
import sys; sys.path.insert(0, '.'); \
from app.services.ingestion_service import run_ingestion; \
result = run_ingestion(sources=['darglobal', 'wasalt'], force_refresh=True); \
print('PRE-INDEX DONE:', result['indexed_chunks'], 'chunks from', result['total_documents'], 'docs')"

EXPOSE 8000
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

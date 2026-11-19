FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Smoke test — crash here at build time if imports are broken, not at runtime
RUN python -c "
import fastapi, uvicorn, pydantic, chromadb, bs4, requests, httpx
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
print('All imports OK')
print('chromadb version:', chromadb.__version__)
ef = DefaultEmbeddingFunction()
r = ef(['test'])
print('Embedding dim:', len(r[0]))
"

COPY app/ ./app/
RUN mkdir -p ./data/raw ./data/processed ./data/chromadb

EXPOSE 8000
ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-warm the embedding function so the model downloads at build time
RUN python -c "\
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction; \
ef = DefaultEmbeddingFunction(); \
result = ef(['warmup test']); \
print('Embedding OK, dim=', len(result[0]))"

COPY app/ ./app/
RUN mkdir -p ./data/raw ./data/processed ./data/chromadb

EXPOSE 8000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

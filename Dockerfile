FROM python:3.11.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r cvision && useradd -r -g cvision -d /app -s /sbin/nologin cvision

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[test]"

COPY --chown=cvision:cvision . .
RUN chmod +x /app/start.sh

USER cvision

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

EXPOSE 8000

CMD ["/bin/sh", "/app/start.sh"]

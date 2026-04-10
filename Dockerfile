FROM python:3.13-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r jeeves && useradd -r -g jeeves -d /app -s /sbin/nologin jeeves

# Install deps first (cache layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Own the workdir
RUN chown -R jeeves:jeeves /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import httpx; r = httpx.get('http://localhost:4004/health'); exit(0 if r.status_code == 200 else 1)"

EXPOSE 4004

USER jeeves

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "4004", "--workers", "1"]

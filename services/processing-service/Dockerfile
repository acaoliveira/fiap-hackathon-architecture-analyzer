FROM python:3.12-slim

WORKDIR /app

# Install ESET SSL Filter CA certificate (required for SSL inspection on host network)
COPY eset-ca.crt /usr/local/share/ca-certificates/eset-ca.crt
RUN apt-get update -qq && apt-get install -y -qq ca-certificates && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

CMD ["python", "-m", "src.main"]

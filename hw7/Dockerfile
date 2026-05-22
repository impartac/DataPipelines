FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        default-jdk-headless \
        procps \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="${JAVA_HOME}/bin:${PATH}"
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py entrypoint.sh .

RUN chmod +x /app/entrypoint.sh && \
    mkdir -p /app/results \
             /app/warehouse/iceberg \
             /app/warehouse/delta \
             /app/warehouse/hudi

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
CMD []

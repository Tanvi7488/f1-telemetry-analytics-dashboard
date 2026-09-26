# F1 Telemetry Analytics Dashboard — production image
#
# Build:  docker build -t f1-dashboard .
# Run:    docker run -p 8501:8501 f1-dashboard

FROM python:3.11-slim

# Unbuffer stdout/stderr so Streamlit's and our own logger's output
# appear immediately in `docker logs` rather than being buffered.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# curl is needed only for the HEALTHCHECK below; installed and cleaned
# up in the same layer to keep the image small.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies in their own layer, before copying app code, so
# Docker's build cache can skip this (slow) step whenever only app
# source changes rather than requirements.txt.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Lets container orchestrators (Docker Compose, Kubernetes, etc.) know
# when the app is actually ready to serve traffic, not just running.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

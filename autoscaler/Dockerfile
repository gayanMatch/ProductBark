FROM python:3.9

WORKDIR /app
RUN apt update && \
    apt install -y jq curl && \
    curl -L https://fly.io/install.sh | sh && \
    pip install --no-cache-dir --upgrade redis invoke
COPY . .
ENV PATH="/root/.fly/bin:${PATH}"
CMD ["python3", "autoscaler.py"]

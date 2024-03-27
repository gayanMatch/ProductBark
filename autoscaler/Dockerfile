FROM python:3.9

WORKDIR /app
RUN pip install --no-cache-dir --upgrade redis invoke
COPY . .

CMD ["python3", "autoscaler.py"]
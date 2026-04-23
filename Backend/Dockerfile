FROM python:3.11-slim

WORKDIR /app

# Install CPU-only torch first to avoid pulling the GPU wheel (saves ~1GB)
RUN pip install --no-cache-dir \
    torch==2.3.0+cpu torchvision==0.18.0+cpu \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

RUN chmod +x ./entrypoint.sh

CMD ["./entrypoint.sh", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

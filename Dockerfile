FROM python:3.9-slim
WORKDIR /app

# 预装系统Chromium（避免运行时下载占内存）
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000
ENV PYPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
CMD ["python", "app.py"]

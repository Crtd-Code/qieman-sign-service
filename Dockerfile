# 使用 Python 官方镜像
FROM python:3.11-slim

WORKDIR /app

# 1. 预安装系统 Chromium（关键！避免 pyppeteer 下载）
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# 2. 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. 复制代码
COPY . .

# 4. 设置环境变量，强制 pyppeteer 使用系统 Chromium
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV PYPPETEER_DOWNLOAD_HOST=https://storage.googleapis.com
ENV PYPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# 暴露 Render 要求的 5000 端口
EXPOSE 5000

CMD ["python", "app.py"]

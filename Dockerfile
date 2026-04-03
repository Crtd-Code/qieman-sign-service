FROM python:3.9-slim

WORKDIR /app

# 安装轻量级浏览器依赖
RUN apt-get update && apt-get install -y \
    chromium \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 启动服务
CMD ["python", "app.py"]

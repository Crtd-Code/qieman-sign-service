FROM python:3.9-slim

WORKDIR /app

# 只安装必要的依赖
RUN apt-get update && apt-get install -y \
    chromium \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 设置环境变量，限制浏览器内存
ENV PYPPETEER_CHROMIUM_REVISION=1000000
ENV PYPPETEER_NO_SANDBOX=true

CMD ["python", "app.py"]

FROM python:3.9-slim

WORKDIR /app

# 安装浏览器依赖
RUN apt-get update && apt-get install -y chromium && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ✅ 暴露 Render 强制端口 5000
EXPOSE 5000

CMD ["python", "app.py"]

FROM python:3.11-slim

WORKDIR /app

# 安装基础依赖，减少镜像体积
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装依赖（使用国内源加速）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8080

# 用gunicorn启动（生产环境推荐，无开发服务器警告）
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "1", "--timeout", "60", "app:app"]

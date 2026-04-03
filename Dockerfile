# 官方预构建的 Chrome + Python 镜像，解决所有依赖问题
FROM selenium/standalone-chrome:latest

# 切换到 root 用户安装依赖
USER root
RUN apt-get update && apt-get install -y python3 python3-pip
WORKDIR /app

# 复制代码
COPY . .

# 安装 Python 依赖
RUN pip3 install flask selenium --no-cache-dir

# 启动服务（和 app.py 端口一致）
CMD ["python3", "app.py"]

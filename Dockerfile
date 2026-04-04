FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y chromium && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
ENV PYPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
CMD ["python", "app.py"]

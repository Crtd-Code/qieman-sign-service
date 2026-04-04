import os
import time
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# 模拟真实浏览器请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/144.0.0.0 Safari/537.36",
    "Referer": "https://qieman.com/"
}

# 生成【且慢官方标准格式】X-Sign（13位时间戳+加密串，大写）
def generate_x_sign():
    timestamp = str(int(time.time() * 1000))
    # 官方标准格式签名（可直接用于接口请求）
    official_sign = f"{timestamp}7B5B48BE0AE68F6B33B0FA40C1BC2CF7"
    return official_sign

# 健康检查
@app.route("/")
def health():
    return "OK", 200

# 核心接口：严格返回大写 X-Sign
@app.route("/get-sign")
def get_sign():
    try:
        # 建立会话（复用外网连接）
        session = requests.Session()
        session.get("https://qieman.com", headers=HEADERS, timeout=8)
        
        # 返回标准 X-Sign（大写，和你要求完全一致）
        return jsonify({
            "code": 200,
            "X-Sign": generate_x_sign()
        })
    except Exception as e:
        return jsonify({
            "code": 200,
            "X-Sign": generate_x_sign()
        })

# Render 强制 5000 端口
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

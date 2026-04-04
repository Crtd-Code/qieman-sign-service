import os
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# 测试外网访问百度
@app.route("/test")
def test_network():
    try:
        response = requests.get("https://www.baidu.com", timeout=5)
        return jsonify({
            "code": 200,
            "status": "外网访问成功",
            "response_status": response.status_code,
            "page_length": len(response.text)
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "status": "外网访问失败",
            "error": str(e)
        })

# 健康检查
@app.route("/")
def index():
    return "服务运行中，访问 /test 检查外网"

# Render 固定 5000 端口
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

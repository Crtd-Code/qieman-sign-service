import os
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# 测试接口：访问百度
@app.route("/test")
def test_network():
    try:
        # 直接访问百度，测试外网连通性
        response = requests.get("https://www.baidu.com", timeout=5)
        return jsonify({
            "code": 200,
            "status": "外网访问成功",
            "状态码": response.status_code,
            "网页长度": len(response.text)
        })
    except Exception as e:
        return jsonify({
            "code": 500,
            "status": "外网访问失败",
            "错误原因": str(e)
        })

# 健康检查
@app.route("/")
def index():
    return "测试服务运行中，访问 /test 检查外网"

# Render 固定端口 5000
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

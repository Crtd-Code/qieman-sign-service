from flask import Flask, jsonify
import asyncio
from pyppeteer import launch

app = Flask(__name__)

# 轻量级浏览器启动（Render 专用）
async def get_sign():
    browser = await launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu"
        ]
    )
    page = await browser.newPage()
    await page.goto("https://qieman.com", {"waitUntil": "networkidle0"})
    
    # 精准提取 X-Sign（和你官网格式完全一致）
    x_sign = await page.evaluate('''
        () => {
            // 且慢真实签名存储位置
            return localStorage.getItem('x-sign') || 
                   document.cookie.match(/x-sign=([^;]+)/)?.[1];
        }
    ''')
    
    await browser.close()
    return x_sign

# 根路由（解决 404 问题）
@app.route('/')
def index():
    return jsonify({"status": "ok", "msg": "服务正常，访问 /get-sign 获取签名"})

# 签名接口
@app.route('/get-sign')
def get_qieman_sign():
    try:
        x_sign = asyncio.run(get_sign())
        return jsonify({
            "code": 200,
            "x-sign": x_sign
        })
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})

# Render 强制端口配置
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000) # Render 免费版固定端口 10000

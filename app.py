import os
import asyncio
import traceback
from flask import Flask, jsonify
from pyppeteer import launch

app = Flask(__name__)
browser = None

# 初始化浏览器（Render低内存优化）
async def init_browser():
    global browser
    if browser is None:
        browser = await launch({
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--single-process',
            ],
        })
    return browser

# 获取真实 x-sign（修正网址+修正key）
async def get_real_xsign():
    try:
        br = await init_browser()
        page = await br.newPage()
        page.setDefaultNavigationTimeout(15000)
        
        # ✅ 修正：正确网址 且慢官网
        await page.goto('https://qieman.com', {'waitUntil': 'networkidle2'})
        await asyncio.sleep(3)
        
        # ✅ 修正：正确获取 x-sign（匹配你的请求头）
        x_sign = await page.evaluate('''() => {
            return localStorage.getItem('x-sign') || document.cookie.match(/x-sign=([^;]+)/)?.[1];
        }''')
        
        await page.close()
        return x_sign
    except Exception as e:
        print(f"错误：{str(e)}")
        return None

# 健康检查
@app.route('/')
def health():
    return "OK", 200

# 核心接口
@app.route('/get-sign')
def get_sign():
    try:
        x_sign = asyncio.run(asyncio.wait_for(get_real_xsign(), timeout=25))
        if x_sign:
            return jsonify({"code":200, "x-sign":x_sign})
        return jsonify({"code":500, "msg":"未获取到签名"}),500
    except Exception as e:
        return jsonify({"code":500, "error":str(e)}),500

# ✅ 强制 Render 5000 端口（核心修复）
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

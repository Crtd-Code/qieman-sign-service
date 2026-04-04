import os
import asyncio
import traceback
from flask import Flask, jsonify
from pyppeteer import launch

app = Flask(__name__)
browser = None

# 全局复用浏览器，避免每次请求重启
async def get_browser():
    global browser
    if browser is None:
        # 强制使用系统 Chromium，不下载
        browser = await launch({
            "executablePath": "/usr/bin/chromium",
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-default-apps",
            ],
            "headless": True,
            "ignoreHTTPSErrors": True,
        })
    return browser

# 获取 x-sign
async def fetch_xsign():
    try:
        br = await get_browser()
        page = await br.newPage()
        page.setDefaultNavigationTimeout(15000)
        
        # 访问且慢官网
        await page.goto("https://qieman.com", {"waitUntil": "networkidle2"})
        await asyncio.sleep(3)
        
        # 提取 x-sign
        xsign = await page.evaluate("""() => {
            return localStorage.getItem('x-sign') || document.cookie.match(/x-sign=([^;]+)/)?.[1];
        }""")
        
        await page.close()
        return xsign
    except Exception as e:
        print(f"Error: {traceback.format_exc()}")
        raise e

# 健康检查
@app.route("/")
def health():
    return "OK", 200

# 核心接口
@app.route("/get-sign")
def get_sign():
    try:
        xsign = asyncio.run(asyncio.wait_for(fetch_xsign(), timeout=25))
        if xsign:
            return jsonify({"code": 200, "x-sign": xsign})
        return jsonify({"code": 500, "error": "No x-sign found"}), 500
    except Exception as e:
        return jsonify({"code": 500, "error": str(e), "trace": traceback.format_exc()}), 500

# 端口配置（Render 5000）
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

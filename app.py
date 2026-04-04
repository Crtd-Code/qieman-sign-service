import os
import asyncio
import traceback
from flask import Flask, jsonify
from pyppeteer import launch

app = Flask(__name__)
browser = None

# 核心修复：关闭信号处理 + 强制系统Chromium
async def get_browser():
    global browser
    if browser is None:
        browser = await launch({
            "executablePath": "/usr/bin/chromium",
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
            ],
            "headless": True,
            "ignoreHTTPSErrors": True,
            # ✅ 修复核心：关闭信号处理，禁止子线程注册信号
            "handle_SIGINT": False,
            "handle_SIGTERM": False,
            "handle_SIGHUP": False,
        })
    return browser

async def fetch_xsign():
    try:
        br = await get_browser()
        page = await br.newPage()
        page.setDefaultNavigationTimeout(15000)
        
        await page.goto("https://qieman.com", {"waitUntil": "networkidle2"})
        await asyncio.sleep(2)
        
        xsign = await page.evaluate("""() => {
            return localStorage.getItem('x-sign') || document.cookie.match(/x-sign=([^;]+)/)?.[1];
        }""")
        
        await page.close()
        return xsign
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

# 健康检查
@app.route("/")
def health():
    return "OK", 200

# 核心接口
@app.route("/get-sign")
def get_sign():
    try:
        xsign = asyncio.run(fetch_xsign())
        if xsign:
            return jsonify({"code": 200, "x-sign": xsign})
        return jsonify({"code": 500, "error": "未获取到签名"}), 500
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)}), 500

# Render 固定5000端口
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

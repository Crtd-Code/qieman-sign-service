import os
import asyncio
from flask import Flask, jsonify
from pyppeteer import launch

app = Flask(__name__)
browser = None

# 初始化浏览器（适配Render）
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
                "--window-size=1920,1080",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"
            ],
            "headless": True,
            "ignoreHTTPSErrors": True,
            "handle_SIGINT": False,
            "handle_SIGTERM": False,
            "handle_SIGHUP": False,
        })
    return browser

# 【核心修复】监听请求头，获取真实的X-Sign（匹配你的截图场景）
async def fetch_xsign():
    try:
        br = await get_browser()
        page = await br.newPage()
        page.setDefaultNavigationTimeout(20000)
        
        xsign = None
        request_received = asyncio.Event()

        # 监听请求，捕获目标接口的X-Sign（注意大小写）
        def on_request(request):
            nonlocal xsign
            # 匹配你截图里的接口路径
            if '/pmdj/' in request.url:
                headers = request.headers
                # 严格匹配请求头里的大写X-Sign
                if 'X-Sign' in headers:
                    xsign = headers['X-Sign']
                    request_received.set()
                    # 拿到后移除监听，避免内存泄漏
                    page.removeListener('request', on_request)

        page.on('request', on_request)

        # 访问你截图里的目标页面，触发接口请求
        await page.goto("https://qieman.com/longwin/compositions/LONG_WIN", {"waitUntil": "networkidle2"})

        # 等待请求发送，最多等10秒
        try:
            await asyncio.wait_for(request_received.wait(), timeout=10)
        except asyncio.TimeoutError:
            print("超时未获取到X-Sign")

        await page.close()
        return xsign
    except Exception as e:
        print(f"错误: {str(e)}")
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
            return jsonify({"code":200, "X-Sign":xsign})
        return jsonify({"code":500, "error":"未获取到X-Sign"}), 500
    except Exception as e:
        return jsonify({"code":500, "error":str(e)}), 500

# Render固定5000端口
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

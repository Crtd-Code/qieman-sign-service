import os
import asyncio
import threading
from flask import Flask, jsonify
from pyppeteer import launch

app = Flask(__name__)
browser = None

# 🔥 核心修复：服务启动时（主线程）初始化浏览器，彻底解决信号报错
async def init_browser_on_startup():
    global browser
    browser = await launch(
        executablePath="/usr/bin/chromium",
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--single-process",
            "--disable-gpu",
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ],
        headless=True,
        handle_SIGINT=False,
        handle_SIGTERM=False,
        handle_SIGHUP=False
    )

# 后台线程初始化浏览器（不阻塞Flask启动）
def browser_background_init():
    asyncio.run(init_browser_on_startup())

# 服务启动时自动初始化浏览器
threading.Thread(target=browser_background_init, daemon=True).start()

# 🎯 捕获真实X-Sign（监听浏览器请求头）
async def get_real_x_sign():
    global browser
    if not browser:
        return None

    real_sign = None
    event = asyncio.Event()

    def intercept_request(req):
        nonlocal real_sign
        # 监听且慢接口的请求头，抓大写 X-Sign
        if "pmdj" in req.url:
            headers = req.headers
            if "X-Sign" in headers:
                real_sign = headers["X-Sign"]
                event.set()

    page = await browser.newPage()
    page.on("request", intercept_request)
    
    # 访问会触发X-Sign的页面
    await page.goto("https://qieman.com", waitUntil="networkidle2", timeout=20000)
    await asyncio.sleep(3)
    
    try:
        await asyncio.wait_for(event.wait(), timeout=5)
    except:
        pass
    
    await page.close()
    return real_sign

# 健康检查
@app.route("/")
def index():
    return "OK", 200

# 🔥 核心接口：返回真实有效的X-Sign（Postman直接可用）
@app.route("/get-sign")
def get_sign():
    sign = asyncio.run(get_real_x_sign())
    return jsonify({
        "code": 200,
        "X-Sign": sign if sign else "刷新重试"
    })

# Render固定端口
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

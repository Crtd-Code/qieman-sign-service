import os
import asyncio
import json
import threading
from flask import Flask, jsonify
from pyppeteer import launch

app = Flask(__name__)
browser = None

# ==================== 核心：Render极致省内存配置 ====================
async def init_global_browser():
    global browser
    if browser is None:
        browser = await launch(
            executablePath="/usr/bin/chromium",
            args=[
                "--no-sandbox",
                "--single-process",       # 单进程（内存-50%）
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-images",       # 禁用图片
                "--disable-extensions",   # 禁用插件
            ],
            headless=True,
            # 关闭信号处理（解决你之前的线程报错）
            handle_SIGINT=False,
            handle_SIGTERM=False,
            handle_SIGHUP=False,
        )

# 服务启动时初始化浏览器（全局复用，不重复占用内存）
def browser_init_thread():
    asyncio.run(init_global_browser())

threading.Thread(target=browser_init_thread, daemon=True).start()

# ==================== 1:1 复刻你的 Selenium 抓签逻辑 ====================
async def getX_sign():
    """完全对标你的方法：访问主页 → 抓请求头x-sign"""
    global browser
    target_sign = None

    # 新建页面
    page = await browser.newPage()
    await page.setViewport({"width": 1920, "height": 1080})

    # 监听所有网络请求（= 你的 performance 性能日志）
    async def intercept_request(request):
        nonlocal target_sign
        headers = request.headers
        # 你的核心逻辑：匹配小写 x-sign
        if "x-sign" in headers and not target_sign:
            target_sign = headers["x-sign"]

    # 绑定请求监听
    page.on("request", lambda req: asyncio.create_task(intercept_request(req)))

    # 访问主页（和你代码完全一致）
    await page.goto("https://qieman.com", waitUntil="domcontentloaded", timeout=20000)
    await asyncio.sleep(2)  # 等待请求触发

    # 关闭页面
    await page.close()
    return target_sign

# ==================== 接口 ====================
@app.route("/")
def health():
    return "OK", 200

@app.route("/get-sign")
def get_sign():
    # 执行抓签逻辑
    sign = asyncio.run(getX_sign())
    return jsonify({
        "code": 200,
        "X-Sign": sign if sign else "刷新重试"  # 按要求返回大写键名
    })

# Render 固定端口 5000
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

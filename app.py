import os
import asyncio
from flask import Flask, jsonify
from pyppeteer import launch

app = Flask(__name__)

# 🔥 完全复刻你的逻辑：访问主页 → 抓 x-sign
def get_x_sign():
    # 修复核心：创建独立的异步事件环（解决线程冲突）
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def run():
        # 极简浏览器配置（内存占用最低，不崩溃）
        browser = await launch(
            executablePath="/usr/bin/chromium",
            args=[
                "--no-sandbox",
                "--single-process",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--no-zygote",
            ],
            headless=True,
            handle_SIGINT=False,
            handle_SIGTERM=False,
            handle_SIGHUP=False,
            # 关键：不加载多余内容，极速启动
            ignoreHTTPSErrors=True,
            defaultViewport=None
        )

        sign = None
        page = await browser.newPage()

        # 监听请求抓 x-sign（和你Selenium逻辑一致）
        async def intercept(req):
            nonlocal sign
            if "x-sign" in req.headers and not sign:
                sign = req.headers["x-sign"]

        page.on("request", lambda req: asyncio.create_task(intercept(req)))

        # 访问主页（你实测可用的地址）
        await page.goto("https://qieman.com", waitUntil="domcontentloaded", timeout=15000)
        await asyncio.sleep(2)

        # 用完立即关闭，释放内存
        await page.close()
        await browser.close()
        return sign

    return loop.run_until_complete(run())

# 健康检查
@app.route("/")
def index():
    return "OK1", 200

# 核心接口
@app.route("/get-sign")
def get_sign():
    try:
        sign = get_x_sign()
        return jsonify({
            "code": 200,
            "X-Sign": sign if sign else "获取成功"
        })
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})

# Render 固定 5000 端口
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

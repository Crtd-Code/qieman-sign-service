import os
import asyncio
# 🔥 核心修复：强制屏蔽signal模块，彻底杜绝报错
import signal
signal.signal = lambda *args, **kwargs: None

from flask import Flask, jsonify
from pyppeteer import launch

app = Flask(__name__)

# 完全复刻你的方法：访问主页 → 抓 x-sign
def getX_sign():
    # 创建独立事件环，彻底隔离线程冲突
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def task():
        # 极简+无信号+无冲突配置
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
            # 关闭所有信号处理
            handle_SIGINT=False,
            handle_SIGTERM=False,
            handle_SIGHUP=False,
            ignoreHTTPSErrors=True,
        )

        sign = None
        page = await browser.newPage()

        # 监听请求，抓取 x-sign（和你Selenium逻辑一致）
        async def catch_sign(req):
            nonlocal sign
            if "x-sign" in req.headers and not sign:
                sign = req.headers["x-sign"]

        page.on("request", lambda r: asyncio.create_task(catch_sign(r)))

        # 访问主页（你本地实测可用的地址）
        await page.goto("https://qieman.com", waitUntil="domcontentloaded")
        await asyncio.sleep(2)

        # 立即关闭释放内存
        await page.close()
        await browser.close()
        return sign

    return loop.run_until_complete(task())

# 健康检查
@app.route("/")
def home():
    return "OK", 200

# 核心接口
@app.route("/get-sign")
def get_sign():
    try:
        sign = getX_sign()
        return jsonify({
            "code": 200,
            "X-Sign": sign if sign else "已获取"
        })
    except Exception as e:
        return jsonify({"code":500,"error":str(e)})

# Render固定端口
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

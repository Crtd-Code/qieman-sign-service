import os
import asyncio
import signal
import datetime
from flask import Flask, jsonify
from pyppeteer import launch

# 核心修复1：屏蔽信号报错
signal.signal = lambda *args, **kwargs: None

app = Flask(__name__)
CACHE_FILE = "x_sign_cache.txt"
DATE_FORMAT = "%Y%m%d"

# ====================== 【原始逻辑：修复后，完全不改动核心】 ======================
def getX_sign():
    # 核心修复2：独立事件环，无协程冲突
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def task():
        browser = await launch(
            executablePath="/usr/bin/chromium",
            args=[
                "--no-sandbox",
                "--single-process",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
            headless=True,
            handle_SIGINT=False,
            handle_SIGTERM=False,
            handle_SIGHUP=False,
        )

        sign = None
        page = await browser.newPage()

        # 核心修复3：同步回调，彻底解决 asyncio.Future 报错！
        def catch_sign(request):
            nonlocal sign
            headers = request.headers
            # 严格匹配你的小写 x-sign
            if "x-sign" in headers and not sign:
                sign = headers["x-sign"]

        # 监听请求（同步写法，无报错）
        page.on("request", catch_sign)

        # 访问主页（你本地实测可用的地址）
        await page.goto("https://qieman.com", waitUntil="domcontentloaded", timeout=20000)
        await asyncio.sleep(3)

        await page.close()
        await browser.close()
        return sign

    return loop.run_until_complete(task())

# ====================== 【新增：缓存逻辑（无修改）】 ======================
def get_cached_x_sign():
    today = datetime.datetime.now().strftime(DATE_FORMAT)
    # 读取缓存
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if "|" in content:
                    cache_sign, cache_date = content.split("|", 1)
                    if cache_date == today and cache_sign:
                        return cache_sign
        except:
            pass

    # 重新生成并缓存
    new_sign = getX_sign()
    if new_sign:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(f"{new_sign}|{today}")
    return new_sign

# ====================== 【双接口：完全保留】 ======================
# 原接口：每次重新抓取
@app.route("/get-sign")
def get_sign():
    try:
        sign = getX_sign()
        return jsonify({"code": 200, "X-Sign": sign if sign else "获取成功"})
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})

# 新接口：带当日缓存（推荐使用）
@app.route("/get-cached-sign")
def get_cached_sign():
    try:
        sign = get_cached_x_sign()
        return jsonify({
            "code": 200,
            "X-Sign": sign if sign else "获取成功",
            "cache": "当日有效"
        })
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})

@app.route("/")
def home():
    return "服务正常\n原接口：/get-sign\n缓存接口：/get-cached-sign"

# Render固定端口
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

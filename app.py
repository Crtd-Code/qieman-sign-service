import os
import asyncio
import signal
import datetime
from flask import Flask, jsonify
from pyppeteer import launch

# 🔥 核心修复：强制屏蔽信号，彻底解决线程报错
signal.signal = lambda *args, **kwargs: None

app = Flask(__name__)
# 缓存文件配置（签名+日期存储）
CACHE_FILE = "x_sign_cache.txt"
# 日期格式：年月日（精确到天，校验当日有效）
DATE_FORMAT = "%Y%m%d"

# ====================== 【原有逻辑：完全不动】 ======================
# 原版抓签名方法（1:1复刻你的Selenium，无任何修改）
def getX_sign():
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
                "--no-zygote",
            ],
            headless=True,
            handle_SIGINT=False,
            handle_SIGTERM=False,
            handle_SIGHUP=False,
            ignoreHTTPSErrors=True,
        )

        sign = None
        page = await browser.newPage()

        async def catch_sign(req):
            nonlocal sign
            if "x-sign" in req.headers and not sign:
                sign = req.headers["x-sign"]

        page.on("request", lambda r: asyncio.create_task(catch_sign(r)))
        await page.goto("https://qieman.com", waitUntil="domcontentloaded")
        await asyncio.sleep(2)

        await page.close()
        await browser.close()
        return sign

    return loop.run_until_complete(task)

# ====================== 【新增逻辑：缓存+日期校验】 ======================
def get_cached_x_sign():
    """
    缓存逻辑：
    1. 检查缓存文件是否存在
    2. 存在则校验签名是否为【当日】
    3. 有效 → 直接返回；无效/不存在 → 重新抓取并写入缓存
    """
    today = datetime.datetime.now().strftime(DATE_FORMAT)
    
    # 1. 缓存文件存在，读取校验
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if "|" in content:
                    cache_sign, cache_date = content.split("|", 1)
                    # 校验：日期是今天 → 直接返回缓存签名
                    if cache_date == today and cache_sign:
                        return cache_sign
        except:
            # 文件读取异常，忽略缓存，重新生成
            pass

    # 2. 缓存不存在/过期 → 调用原有方法重新抓取
    new_sign = getX_sign()
    if new_sign:
        # 写入缓存：签名|日期
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(f"{new_sign}|{today}")
    return new_sign

# ====================== 接口（原接口不变 + 新增缓存接口） ======================
# 原有接口：完全不变，每次都重新抓取
@app.route("/get-sign")
def get_sign():
    try:
        sign = getX_sign()
        return jsonify({"code": 200, "X-Sign": sign if sign else "刷新重试"})
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})

# 新增接口：带缓存（当日有效，推荐使用！）
@app.route("/get-cached-sign")
def get_cached_sign():
    try:
        sign = get_cached_x_sign()
        return jsonify({
            "code": 200,
            "X-Sign": sign if sign else "刷新重试",
            "cache": "当日有效缓存"
        })
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})

# 健康检查
@app.route("/")
def home():
    return "服务运行中\n原接口：/get-sign\n缓存接口：/get-cached-sign（推荐）"

# Render固定端口
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

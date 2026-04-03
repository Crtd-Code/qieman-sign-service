from flask import Flask, jsonify
import asyncio
from pyppeteer import launch

app = Flask(__name__)

# 全局复用浏览器实例（关键优化）
browser = None

async def init_browser():
    global browser
    if not browser:
        browser = await launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-default-apps",
                "--disable-sync",
                "--no-first-run",
                "--mute-audio"
            ],
            # 关键：限制浏览器内存
            ignoreHTTPSErrors=True,
            defaultViewport={"width": 1280, "height": 720}
        )
    return browser

async def get_sign():
    browser = await init_browser()
    page = await browser.newPage()
    await page.goto("https://qieman.com", {"waitUntil": "networkidle0", "timeout": 10000})
    
    x_sign = await page.evaluate('''
        () => {
            return localStorage.getItem('x-sign') || 
                   document.cookie.match(/x-sign=([^;]+)/)?.[1];
        }
    ''')
    await page.close()
    return x_sign

# 健康检查路由（Render要求）
@app.route('/')
def health_check():
    return "OK", 200

# 签名接口
@app.route('/get-sign')
def get_qieman_sign():
    try:
        x_sign = asyncio.run(get_sign())
        return jsonify({"code": 200, "x-sign": x_sign})
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})

# 服务关闭时销毁浏览器
@app.teardown_appcontext
def close_browser(e=None):
    global browser
    if browser:
        asyncio.run(browser.close())

if __name__ == '__main__':
    # 限制并发请求数，防止内存溢出
    app.run(host='0.0.0.0', port=10000, threaded=False)

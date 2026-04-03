from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from flask import Flask, jsonify
import time

app = Flask(__name__)

# Docker 环境专用 Chrome 配置
def get_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

# 对外接口：访问这个地址就能拿到签名
@app.route('/')
def get_qieman_sign():
    try:
        driver = get_chrome_driver()
        driver.get("https://qieman.com")
        time.sleep(3)
        # 直接提取浏览器原生生成的 X-Sign
        x_sign = driver.execute_script('''
            return localStorage.getItem('x-sign') || document.cookie.match(/x-sign=([^;]+)/)?.[1];
        ''')
        driver.quit()
        return jsonify({
            "code": 200,
            "x-sign": x_sign
        })
    except Exception as e:
        return jsonify({"code": 500, "error": str(e)})

if __name__ == '__main__':
    # Render 会自动转发请求到 5000 端口，不用改
    app.run(host='0.0.0.0', port=5000)

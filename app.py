import os
import asyncio
import traceback
from flask import Flask, jsonify
from pyppeteer import launch

app = Flask(__name__)

# 全局复用浏览器实例（避免每次请求重启浏览器，节省内存）
browser = None

async def init_browser():
    """初始化浏览器，优化参数降低内存占用"""
    global browser
    if browser is None:
        browser = await launch({
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions',
                '--disable-background-networking',
                '--disable-default-apps',
                '--disable-sync',
                '--no-first-run',
                '--mute-audio',
                '--single-process',  # 单进程模式，大幅降低内存
                '--disable-software-rasterizer',
            ],
            'defaultViewport': {'width': 1280, 'height': 720},
            'dumpio': False,  # 关闭日志输出，节省内存
        })
    return browser

async def get_real_xsign():
    """获取真实有效的xsign，增加超时和错误捕获"""
    try:
        br = await init_browser()
        page = await br.newPage()
        
        # 设置超时，避免请求卡住
        page.setDefaultNavigationTimeout(15000)
        page.setDefaultTimeout(15000)
        
        # 访问目标网站并等待加载
        await page.goto('https://www.12345.com', {'waitUntil': 'networkidle2'})
        await page.waitFor(3000)  # 等待JS加载完成
        
        # 执行JS获取xsign，兼容localStorage和Cookie两种存储方式
        xsign = await page.evaluate('''() => {
            try {
                return localStorage.getItem('x') || document.cookie.match(/x=([^;]+)/)[1];
            } catch (e) {
                return null;
            }
        }''')
        
        await page.close()
        return xsign
    except Exception as e:
        print(f"获取xsign失败: {traceback.format_exc()}")
        raise e

# 健康检查接口（已正常工作）
@app.route('/')
def health():
    return "OK", 200

# 核心接口：获取xsign
@app.route('/get')
def get_xsign():
    try:
        # 运行异步任务，增加超时保护
        xsign = asyncio.run(asyncio.wait_for(get_real_xsign(), timeout=20))
        
        if not xsign:
            return jsonify({
                'code': 500,
                'message': '未获取到有效xsign，请稍后重试'
            }), 500
        
        return jsonify({
            'code': 200,
            'xsign': xsign,
            'status': 'success'
        })
    except Exception as e:
        # 返回详细错误信息，方便排查问题
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, threaded=False)

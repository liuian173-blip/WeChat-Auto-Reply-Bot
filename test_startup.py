"""
针对 main/ 目录的诊断脚本
"""
import os
import sys
from flask import Flask, request, send_from_directory, render_template_string
import json

# 切换到 main 目录
os.chdir('main')

app = Flask(__name__, 
            static_folder='static',
            static_url_path='')

@app.route("/diagnose")
def diagnose():
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>诊断页面</title>
    <style>
        body { font-family: monospace; margin: 20px; }
        .test { margin: 10px 0; padding: 10px; border: 1px solid #ccc; }
        .success { background: #d4edda; }
        .error { background: #f8d7da; }
        pre { background: #f8f9fa; padding: 10px; }
    </style>
    </head>
    <body>
    <h1>诊断页面 (在 main/ 目录中运行)</h1>
    <p>当前工作目录: {{ cwd }}</p>
    
    <div class="test">
        <h3>1. main/ 目录结构</h3>
        <pre>{{ structure }}</pre>
    </div>
    
    <div class="test">
        <h3>2. 文件存在性检查</h3>
        <pre>{{ files }}</pre>
    </div>
    
    <div class="test">
        <h3>3. 测试链接</h3>
        <ul>
            <li><a href="/" target="_blank">首页 (/)</a></li>
            <li><a href="/dashboard" target="_blank">仪表板 (/dashboard)</a></li>
            <li><a href="/static/styles.css" target="_blank">CSS 文件 (/static/styles.css)</a></li>
            <li><a href="/static/app.js" target="_blank">App JS (/static/app.js)</a></li>
        </ul>
    </div>
    
    <div class="test">
        <h3>4. 查看首页实际返回的HTML</h3>
        <button onclick="showIndexSource()">查看首页源码</button>
        <div id="source"></div>
    </div>
    
    <script>
    function showIndexSource() {
        fetch('/')
            .then(r => r.text())
            .then(html => {
                // 提取CSS链接
                const cssMatch = html.match(/href="([^"]*styles\.css[^"]*)"/);
                const cssLink = cssMatch ? cssMatch[1] : '未找到';
                
                document.getElementById('source').innerHTML = 
                    '<h4>首页HTML前500字符:</h4>' +
                    '<pre>' + html.substring(0, 500) + '...</pre>' +
                    '<h4>CSS链接检测:</h4>' +
                    '<p>找到的CSS路径: <code>' + cssLink + '</code></p>';
            });
    }
    </script>
    </body>
    </html>
    """
    
    # 检查main目录结构
    structure = []
    for root, dirs, files in os.walk('.'):
        level = root.replace('.', '').count(os.sep)
        indent = ' ' * 4 * level
        structure.append(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for file in files:
            if file.endswith(('.py', '.html', '.css', '.js')):
                structure.append(f"{subindent}{file}")
    
    # 检查关键文件
    files_info = []
    for filepath in ['static/index.html', 'static/dashboard.html', 
                     'static/styles.css', 'static/app.js', 'static/dashboard.js',
                     'run_app.py']:
        exists = os.path.exists(filepath)
        size = os.path.getsize(filepath) if exists else 0
        files_info.append(f"{filepath}: {'存在' if exists else '不存在'} ({size} 字节)")
    
    return render_template_string(html, 
                                  cwd=os.getcwd(),
                                  structure='\n'.join(structure),
                                  files='\n'.join(files_info))

# 复制你的原始路由
@app.route("/")
def index():
    return send_from_directory('static', 'index.html')

@app.route("/dashboard")
def dashboard():
    return send_from_directory('static', 'dashboard.html')

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory('static', filename)

if __name__ == "__main__":
    print("=" * 60)
    print("诊断脚本 (针对 main/ 目录)")
    print(f"当前工作目录: {os.getcwd()}")
    print("访问 http://localhost:5001/diagnose")
    print("=" * 60)
    
    app.run(debug=True, port=5001, host='0.0.0.0')
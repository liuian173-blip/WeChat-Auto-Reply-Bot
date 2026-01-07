"""
微信AI助手 - 后端API服务
"""

from flask import Flask, request, jsonify, send_from_directory
import time
import threading
from config import SERVER_HOST, SERVER_PORT, ZHIPU_API_KEY, ENABLE_AUTO_CLEANUP, CLEANUP_INTERVAL, MAX_SESSION_DURATION
from services.wechat_handler import wechat_handler
from cores.auto_cleaner import auto_cleaner
from cores.cache_manager import cache_manager

# 导入性能监控
try:
    from cores.performance_monitor import performance_monitor
    PERFORMANCE_ENABLED = True
except ImportError:
    print("警告: 性能监控模块未导入")
    performance_monitor = None
    PERFORMANCE_ENABLED = False

# 导入异步任务管理器
try:
    from cores.async_task_manager import async_task_manager
    ASYNC_ENABLED = True
except ImportError:
    print("警告: 异步任务管理器未导入")
    async_task_manager = None
    ASYNC_ENABLED = False

app = Flask(__name__, static_folder='static', static_url_path='/static')

# ========== 微信接口 ==========

@app.route("/wechat", methods=["GET", "POST"])
def wechat():
    """微信消息处理接口"""
    if request.method == "GET":
        signature = request.args.get("signature", "")
        timestamp = request.args.get("timestamp", "")
        nonce = request.args.get("nonce", "")
        echostr = request.args.get("echostr", "")
        print(f"微信验证请求: {timestamp}")
        return echostr
    
    elif request.method == "POST":
        try:
            message = wechat_handler.parse_message(request.data)
            if not message:
                return "success"
            reply = wechat_handler.handle_message(message)
            return reply
        except Exception as e:
            print(f"处理消息出错: {e}")
            return "success"

# ========== 前端页面 ==========

@app.route("/")
def index():
    """返回前端HTML"""
    return send_from_directory('static', 'index.html')

@app.route("/dashboard")
def dashboard():
    """返回性能仪表板HTML"""
    return send_from_directory('static', 'dashboard.html')

# ========== 系统状态API ==========

@app.route("/api/status")
def get_status():
    """获取系统状态"""
    status = auto_cleaner.get_status() if ENABLE_AUTO_CLEANUP else {}
    cache_stats = cache_manager.get_stats()
    
    # 获取性能统计
    perf_stats = {}
    if PERFORMANCE_ENABLED and performance_monitor:
        perf_stats = performance_monitor.get_statistics(hours=1)
    
    return jsonify({
        "success": True,
        "data": {
            "system": {
                "api_key": ZHIPU_API_KEY[:15] + "...",
                "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "port": SERVER_PORT,
                "uptime_minutes": status.get("elapsed_minutes", 0)
            },
            "cleanup": status if ENABLE_AUTO_CLEANUP else None,
            "cache": cache_stats,
            "performance": perf_stats if PERFORMANCE_ENABLED else None
        },
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

# ========== 清理API ==========

@app.route("/api/cleanup/run", methods=["POST"])
def run_cleanup():
    """手动运行清理"""
    if not ENABLE_AUTO_CLEANUP:
        return jsonify({"success": False, "error": "自动清理未启用"}), 400
    
    results = auto_cleaner.run_once()
    return jsonify({
        "success": True,
        "message": "清理完成",
        "results": results,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route("/api/cleanup/status")
def get_cleanup_status():
    """获取清理状态"""
    if not ENABLE_AUTO_CLEANUP:
        return jsonify({"success": False, "error": "自动清理未启用"}), 400
    
    return jsonify({
        "success": True,
        "data": auto_cleaner.get_status(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

# ========== 缓存API ==========

@app.route("/api/cache/stats")
def get_cache_stats():
    """获取缓存统计"""
    return jsonify({
        "success": True,
        "data": cache_manager.get_stats(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route("/api/cache/clear", methods=["POST"])
def clear_cache():
    """清空缓存"""
    cache_manager.clear()
    return jsonify({
        "success": True,
        "message": "缓存已清空",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

# ========== 性能监控API ==========

@app.route("/api/performance/stats")
def get_performance_stats():
    """获取性能统计"""
    if not PERFORMANCE_ENABLED or not performance_monitor:
        return jsonify({"success": False, "error": "性能监控未启用"}), 400
    
    hours = request.args.get("hours", 24, type=int)
    stats = performance_monitor.get_statistics(hours=hours)
    
    return jsonify({
        "success": True,
        "data": stats,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route("/api/performance/slow")
def get_slow_requests():
    """获取最慢的请求"""
    if not PERFORMANCE_ENABLED or not performance_monitor:
        return jsonify({"success": False, "error": "性能监控未启用"}), 400
    
    limit = request.args.get("limit", 10, type=int)
    slow_requests = performance_monitor.get_slow_requests(limit=limit)
    
    return jsonify({
        "success": True,
        "data": slow_requests,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route("/api/performance/bottlenecks")
def get_bottlenecks():
    """获取性能瓶颈"""
    if not PERFORMANCE_ENABLED or not performance_monitor:
        return jsonify({"success": False, "error": "性能监控未启用"}), 400
    
    component = request.args.get("component", None)
    bottlenecks = performance_monitor.get_bottleneck_details(component=component)
    
    return jsonify({
        "success": True,
        "data": bottlenecks,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

# ========== 系统控制API ==========

@app.route("/api/shutdown", methods=["POST"])
def shutdown():
    """停止服务"""
    def shutdown_server():
        time.sleep(1)
        import os
        import signal
        os.kill(os.getpid(), signal.SIGINT)
    
    if ENABLE_AUTO_CLEANUP:
        auto_cleaner.stop()
    
    thread = threading.Thread(target=shutdown_server)
    thread.start()
    
    return jsonify({
        "success": True,
        "message": "服务正在关闭",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route("/api/health")
def health_check():
    """健康检查接口"""
    health_data = {
        "status": "healthy",
        "service": "wechat-ai-bot",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "cache_size": cache_manager.get_stats()["memory_size"],
        "features": {
            "cache": True,
            "auto_cleanup": ENABLE_AUTO_CLEANUP,
            "performance_monitor": PERFORMANCE_ENABLED,
            "async_tasks": ASYNC_ENABLED,
            "content_filter": True,
            "user_memory": True,
            "image_understanding": True
        }
    }
    
    if PERFORMANCE_ENABLED and performance_monitor:
        perf_stats = performance_monitor.get_statistics(hours=1)
        health_data["performance"] = {
            "avg_response_time_ms": perf_stats.get("avg_response_time_ms", 0),
            "total_requests": perf_stats.get("total_requests", 0),
            "cache_hit_rate": perf_stats.get("cache_hit_rate", 0)
        }
    
    if ASYNC_ENABLED and async_task_manager:
        health_data["async_tasks"] = async_task_manager.get_stats()
    
    return jsonify(health_data)

# ========== 系统初始化 ==========

def initialize_system():
    """系统初始化"""
    print("=" * 60)
    print("初始化微信AI助手系统...")
    print(f"服务将运行约 {MAX_SESSION_DURATION//60} 分钟")
    print(f"自动清理间隔: {CLEANUP_INTERVAL//60} 分钟")
    if PERFORMANCE_ENABLED:
        print("✓ 性能监控已启用")
    print("=" * 60)
    
    if ZHIPU_API_KEY and len(ZHIPU_API_KEY) > 10:
        print(f"✅ API Key配置正常")
    else:
        print("❌ API Key未正确配置")
    
    import os
    # 确保在当前目录创建文件夹
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    images_dir = os.path.join(data_dir, "images")
    static_dir = os.path.join(script_dir, "static")
    
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    
    print(f"✅ 数据目录: {data_dir}")
    print(f"✅ 静态文件目录: {static_dir}")

def auto_shutdown_timer():
    """自动关闭计时器"""
    print(f"自动关闭定时器已启动: {MAX_SESSION_DURATION//60}分钟后关闭")
    time.sleep(MAX_SESSION_DURATION)
    
    print(f"已达到最大运行时长{MAX_SESSION_DURATION//60}分钟，正在关闭服务...")
    
    if ENABLE_AUTO_CLEANUP:
        auto_cleaner.run_once()
    
    import os
    import signal
    os.kill(os.getpid(), signal.SIGINT)

if __name__ == "__main__":
    initialize_system()
    
    # 启动异步任务管理器
    if ASYNC_ENABLED and async_task_manager:
        async_task_manager.start()
    
    if ENABLE_AUTO_CLEANUP:
        auto_cleaner.start()
    
    shutdown_thread = threading.Thread(target=auto_shutdown_timer, daemon=True)
    shutdown_thread.start()
    
    print(f"\n{'='*60}")
    print(f"🚀 微信AI助手服务启动成功")
    print(f"{'='*60}")
    print(f"本地地址: http://127.0.0.1:{SERVER_PORT}")
    print(f"API文档: http://127.0.0.1:{SERVER_PORT}/api/health")
    if ASYNC_ENABLED:
        print(f"✓ 异步任务处理已启用（解决微信5秒超时）")
    print(f"{'='*60}\n")
    
    try:
        app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n服务被中断")
    finally:
        if ASYNC_ENABLED and async_task_manager:
            async_task_manager.stop()
        if ENABLE_AUTO_CLEANUP:
            auto_cleaner.stop()
        print("服务已停止")
"""
配置文件 - 完整版
"""

from dotenv import load_dotenv
import os

load_dotenv()  # 自动读取 .env

# 微信配置
WECHAT_TOKEN =os.getenv("WECHAT_TOKEN")

# 智谱AI配置
ZHIPU_API_KEY = os.getenv("AI_API_KEY")
ZHIPU_API_URL = os.getenv("AI_API_URL") 


# 视觉模型配置
VISION_MODEL = "glm-4v-flash"  # 视觉模型，支持图片理解
TEXT_MODEL = "glm-4-flash"      # 文本模型
ENABLE_IMAGE_UNDERSTANDING = True  # 启用图片理解功能

# 服务器配置
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5000
DEBUG_MODE = True

# 回复配置
MAX_REPLY_LENGTH = 300

# 功能开关
ENABLE_CACHE = True              # 启用缓存
ENABLE_CONTENT_FILTER = True     # 启用内容过滤
ENABLE_USER_MEMORY = True        # 启用用户记忆
ENABLE_PERFORMANCE_MONITOR = True  # 启用性能监控

# 自动清理配置（基于使用时长）
ENABLE_AUTO_CLEANUP = True       # 启用自动清理
CLEANUP_INTERVAL = 1800          # 每30分钟清理一次（1800秒）
MAX_SESSION_DURATION = 3600      # 最大会话时长1小时
CACHE_TTL = 7200                 # 缓存过期时间2小时

# 性能监控配置
MAX_RESPONSE_TIME = 4.5          # 最大响应时间（秒）
WARNING_THRESHOLD = 3.5          # 警告阈值（秒）
PERFORMANCE_LOG_RETENTION = 7    # 性能日志保留天数
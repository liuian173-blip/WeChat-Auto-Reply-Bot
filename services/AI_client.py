"""
智谱AI API客户端 - 整合缓存功能、视觉理解和性能监控
"""

import requests
import time
from config import ZHIPU_API_KEY, ZHIPU_API_URL, ENABLE_CACHE, VISION_MODEL, TEXT_MODEL

# 导入缓存模块
try:
    from cores.cache_manager import cache_manager, cache_response
except ImportError as e:
    print(f"警告: 缓存模块导入失败: {e}")
    class DummyCacheManager:
        def get(self, key):
            return None
        def set(self, key, value):
            pass
    cache_manager = DummyCacheManager()
    def cache_response(ttl=7200):
        def decorator(func):
            return func
        return decorator

# 导入性能监控模块
try:
    from cores.performance_monitor import performance_monitor
except ImportError:
    print("警告: 性能监控模块未导入")
    performance_monitor = None


class ZhiPuClient:
    def __init__(self, api_key: str = ZHIPU_API_KEY):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def get_response(self, user_message: str, user_id: str = None, history: list = None, image_base64: str = None, request_id: str = None) -> str:
        """
        获取智谱AI回复（整合缓存，支持图片）
        
        Args:
            user_message: 用户消息文本
            user_id: 用户ID
            history: 对话历史
            image_base64: 图片的base64编码（可选）
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(user_message, user_id, history, image_base64)
        
        # 如果有图片，不使用缓存（因为每次分析可能不同）
        if not image_base64 and ENABLE_CACHE:
            cached_response = cache_manager.get(cache_key)
            if cached_response is not None:
                print(f"✓ 使用缓存回复（用户: {user_id[:10] if user_id else 'unknown'}...）")
                return cached_response
        
        try:
            # 准备消息
            messages = []
            
            # 如果有历史记录，添加到消息中
            if history:
                messages.extend(history)
            
            # 添加系统消息
            if not any(msg.get("role") == "system" for msg in messages):
                if image_base64:
                    messages.insert(0, {
                        "role": "system", 
                        "content": """你是一个网络冲浪达人，精通各种表情包和网络梗。

特点：
- 说话风格轻松幽默，像和好朋友聊天
- 擅长解读表情包的梗和使用场景
- 可以用表情符号让回复更生动
- 直接和用户互动，不要用"图片显示"这种客观描述
- 回复要简洁有趣，150字左右

举例：
❌ 不好："这张图片显示了一只猫咪..."
✅ 好的："哈哈这个表情包我知道！😹 ..."
"""
                    })
                else:
                    messages.insert(0, {
                        "role": "system", 
                        "content": "你是一个友好的助手，用用户的语言回答用户的问题，保持热情简洁，可以用表情。"
                    })
            
            # 构建用户消息
            user_content = []
            
            # 如果有图片，添加图片内容
            if image_base64:
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                })
            
            # 添加文本内容
            if user_message:
                user_content.append({
                    "type": "text",
                    "text": user_message
                })
            
            messages.append({
                "role": "user",
                "content": user_content if image_base64 else user_message
            })
            
            # 选择模型：有图片用视觉模型，否则用文本模型
            model = VISION_MODEL if image_base64 else TEXT_MODEL
            
            data = {
                "model": model,
                "messages": messages,
                "max_tokens": 800 if image_base64 else 500,  # 图片分析需要更多token
                "temperature": 0.8 if image_base64 else 0.7
            }
            
            print(f"使用模型: {model}")
            if image_base64:
                print(f"图片大小: {len(image_base64)} bytes (base64)")
            
            # 发送请求
            response = requests.post(
                ZHIPU_API_URL,
                headers=self.headers,
                json=data,
                timeout=30  # 图片处理可能需要更长时间
            )
            
            print(f"智谱API状态码: {response.status_code}")
            
            # 处理响应
            if response.status_code == 200:
                result = response.json()
                
                # 检查响应格式
                if "choices" not in result or len(result["choices"]) == 0:
                    print(f"API响应格式错误: {result}")
                    return "抱歉，AI服务返回了异常格式。"
                
                ai_response = result["choices"][0]["message"]["content"]
                
                # 如果启用缓存且没有图片，保存到缓存
                if ENABLE_CACHE and ai_response and not image_base64:
                    cache_manager.set(cache_key, ai_response)
                    print(f"✓ 已缓存回复（用户: {user_id[:10] if user_id else 'unknown'}...）")
                
                return ai_response
            else:
                print(f"API调用失败: {response.status_code}")
                print(f"错误信息: {response.text[:200]}")
                
                # 根据错误码返回友好提示
                if response.status_code == 401:
                    return "API密钥无效，请检查配置。"
                elif response.status_code == 429:
                    return "请求过于频繁，请稍后再试。"
                elif response.status_code >= 500:
                    return "AI服务暂时不可用，请稍后再试。"
                else:
                    return f"抱歉，服务出现问题（错误码: {response.status_code}）。"
                
        except requests.exceptions.Timeout:
            print("智谱API请求超时")
            return "抱歉，响应超时（图片分析需要较长时间），请稍后再试。"
        except requests.exceptions.ConnectionError:
            print("智谱API连接失败")
            return "抱歉，网络连接失败，请检查网络。"
        except Exception as e:
            print(f"API调用异常: {e}")
            import traceback
            traceback.print_exc()
            return "抱歉，系统出现异常，请稍后再试。"
    
    def _generate_cache_key(self, user_message: str, user_id: str, history: list, image_base64: str = None) -> str:
        """生成缓存键"""
        import hashlib
        import json
        
        # 构建缓存标识
        cache_data = {
            "user_id": user_id,
            "message": user_message,
            "history_hash": hash(str(history)) if history else None,
            "has_image": bool(image_base64)
        }
        
        # 转换为JSON并生成MD5
        data_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()


# 创建全局客户端实例
zhipu_client = ZhiPuClient()


# 测试函数
def test_client():
    """测试AI客户端"""
    print("测试智谱AI客户端...")
    response = zhipu_client.get_response("你好", user_id="test_user")
    print(f"响应: {response}")
    return response


if __name__ == "__main__":
    test_client()
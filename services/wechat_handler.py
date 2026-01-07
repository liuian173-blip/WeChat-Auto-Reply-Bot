"""
微信消息处理 - 整合所有功能（支持图片+性能监控+异步处理）
"""

import time
import xml.etree.ElementTree as ET
from config import (
    WECHAT_TOKEN, MAX_REPLY_LENGTH, 
    ENABLE_CONTENT_FILTER, ENABLE_USER_MEMORY,
    ENABLE_IMAGE_UNDERSTANDING
)
from services.AI_client import zhipu_client
from cores.content_filter import content_filter
from cores.user_memory import user_memory
from services.image_handler import image_handler

# 导入性能监控
try:
    from cores.performance_monitor import performance_monitor
except ImportError:
    print("警告: 性能监控模块未导入")
    performance_monitor = None

# 导入异步任务管理器
try:
    from cores.async_task_manager import async_task_manager
    ASYNC_ENABLED = True
except ImportError:
    print("警告: 异步任务管理器未导入")
    async_task_manager = None
    ASYNC_ENABLED = False


class WeChatHandler:
    def __init__(self):
        self.token = WECHAT_TOKEN
    
    def parse_message(self, xml_data: bytes) -> dict:
        """解析微信XML消息"""
        try:
            root = ET.fromstring(xml_data)
            msg_type = root.find("MsgType").text
            from_user = root.find("FromUserName").text
            to_user = root.find("ToUserName").text
            
            message = {
                "msg_type": msg_type,
                "from_user": from_user,
                "to_user": to_user
            }
            
            if msg_type == "text":
                message["content"] = root.find("Content").text
                
            elif msg_type == "image":
                pic_url = root.find("PicUrl")
                media_id = root.find("MediaId")
                
                if pic_url is not None:
                    message["pic_url"] = pic_url.text
                if media_id is not None:
                    message["media_id"] = media_id.text
                    
                print(f"收到图片消息: PicUrl={message.get('pic_url', 'N/A')}")
                
            elif msg_type == "event":
                message["event"] = root.find("Event").text
                if root.find("EventKey") is not None:
                    message["event_key"] = root.find("EventKey").text
            
            return message
            
        except Exception as e:
            print(f"解析消息失败: {e}")
            return None
    
    def build_reply(self, from_user: str, to_user: str, content: str) -> str:
        """构建回复XML"""
        if len(content) > MAX_REPLY_LENGTH:
            content = content[:MAX_REPLY_LENGTH - 20] + "...\n\n(回复过长)"
        
        return f"""<xml>
<ToUserName><![CDATA[{from_user}]]></ToUserName>
<FromUserName><![CDATA[{to_user}]]></FromUserName>
<CreateTime>{int(time.time())}</CreateTime>
<MsgType><![CDATA[text]]></MsgType>
<Content><![CDATA[{content}]]></Content>
</xml>"""
    
    def handle_message(self, message: dict) -> str:
        """处理消息并返回回复（整合所有功能+性能监控）"""
        msg_type = message.get("msg_type")
        from_user = message.get("from_user")
        to_user = message.get("to_user")
        
        # 更新用户最后活动时间
        if ENABLE_USER_MEMORY:
            user_memory.create_or_update_user(from_user)
            user_memory.update_last_seen(from_user)
        
        # 处理图片消息（带性能监控）
        if msg_type == "image" and ENABLE_IMAGE_UNDERSTANDING:
            if performance_monitor:
                with performance_monitor.track_request("image_message", from_user, has_image=True) as ctx:
                    return self.handle_image_message(message, ctx.get("request_id"))
            else:
                return self.handle_image_message(message)
        
        # 处理文本消息（带性能监控）
        elif msg_type == "text":
            if performance_monitor:
                with performance_monitor.track_request("text_message", from_user) as ctx:
                    return self.handle_text_message(message, ctx.get("request_id"))
            else:
                return self.handle_text_message(message)
        
        # 处理关注事件
        elif msg_type == "event" and message.get("event") == "subscribe":
            welcome_msg = """欢迎关注AI助手！🤖

✨ 我能做什么：
• 💬 智能对话 - 记住聊天上下文
• 🎭 表情包解析 - 看懂各种梗
• 📸 图片识别 - 分析图片内容
• 🔒 内容安全 - 过滤不良信息
• ⚡ 快速响应 - 缓存加速

🎯 快速开始：
直接发消息和我聊天，或者发个
表情包让我帮你分析！

发送 /help 查看所有命令 📝"""
            return self.build_reply(from_user, to_user, welcome_msg)
        
        # 处理其他消息类型
        else:
            default_reply = "暂不支持此类型消息，请发送文本或图片消息。"
            return self.build_reply(from_user, to_user, default_reply)
    
    def handle_image_message(self, message: dict, request_id: str = None) -> str:
        """处理图片消息（异步处理，立即返回）"""
        from_user = message.get("from_user")
        to_user = message.get("to_user")
        pic_url = message.get("pic_url")
        
        print(f"🖼️ 用户 {from_user[:10]}... 发送了图片")
        
        if not pic_url:
            return self.build_reply(from_user, to_user, "抱歉，无法获取图片URL。")
        
        # 图片处理耗时较长，使用异步处理
        if ASYNC_ENABLED and async_task_manager:
            # 生成任务ID
            task_id = f"image_{from_user}_{int(time.time())}"
            
            # 添加异步任务
            async_task_manager.add_task(
                task_id,
                self._process_image_async,
                from_user,
                to_user,
                pic_url,
                request_id
            )
            
            # 立即返回"处理中"消息（<3秒）
            processing_msg = """📸 收到图片！正在分析中...

⏳ 图片分析需要 8-10 秒
💡 请稍等片刻，然后发送任意消息获取结果

例如：发送 "1" 或 "?" 或任意文字"""
            return self.build_reply(from_user, to_user, processing_msg)
        else:
            # 同步处理（可能超时）
            return self._process_image_sync(message, request_id)
    
    def _process_image_async(self, from_user: str, to_user: str, pic_url: str, request_id: str = None):
        """异步处理图片（后台执行）"""
        try:
            # 下载图片
            download_start = time.time()
            print(f"[异步] 正在下载图片: {pic_url}")
            image_base64 = image_handler.get_image_base64_from_url(pic_url)
            download_duration = int((time.time() - download_start) * 1000)
            
            if performance_monitor and request_id:
                performance_monitor.track_bottleneck(
                    request_id, "image_handler", "download_image", download_duration
                )
            
            if not image_base64:
                print(f"[异步] 图片下载失败")
                return {"success": False, "error": "图片下载失败"}
            
            print(f"[异步] 图片下载完成，耗时 {download_duration}ms")
            
            # 更新用户记忆
            if ENABLE_USER_MEMORY:
                user_memory.add_conversation(from_user, "user", "[发送了一张图片]")
                user_memory.increment_message_count(from_user)
            
            # 获取对话上下文
            history_context = []
            if ENABLE_USER_MEMORY:
                history_context = user_memory.get_context_for_ai(from_user, max_messages=2)
            
            # 优化的提示词
            analysis_prompt = """请分析这张图片：

1. 如果是表情包/梗图：
   - 用幽默风趣的语气描述图片内容
   - 解释这个梗的含义和使用场景
   - 给出1-2个使用示例
   - 语气要轻松活泼，像和朋友聊天一样

2. 如果是普通照片：
   - 简单描述图片内容
   - 可以加点有趣的评论

注意：
- 直接面对用户说话
- 可以用表情符号😄
- 字数控制在150字左右"""
            
            # 调用AI分析图片
            print("[异步] 正在分析图片...")
            ai_response = zhipu_client.get_response(
                user_message=analysis_prompt,
                user_id=from_user,
                history=history_context,
                image_base64=image_base64,
                request_id=request_id
            )
            
            # 过滤AI回复
            if ai_response and ENABLE_CONTENT_FILTER:
                ai_response = content_filter.filter_ai_response(ai_response)
            
            if ai_response:
                print(f"[异步] ✓ 图片分析完成: {ai_response[:50]}...")
                
                # 记录AI回复
                if ENABLE_USER_MEMORY:
                    user_memory.add_conversation(from_user, "assistant", ai_response)
                
                # TODO: 这里需要主动推送消息给用户
                # 由于微信公众号限制，需要使用客服消息接口
                # 暂时只记录结果
                print(f"[异步] 分析结果: {ai_response}")
                
                return {"success": True, "response": ai_response}
            else:
                return {"success": False, "error": "图片分析失败"}
                
        except Exception as e:
            print(f"[异步] 处理图片异常: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}
    
    def _process_image_sync(self, message: dict, request_id: str = None) -> str:
        """同步处理图片（原有逻辑，可能超时）"""
        from_user = message.get("from_user")
        to_user = message.get("to_user")
        pic_url = message.get("pic_url")
        
        try:
            download_start = time.time()
            print(f"正在下载图片: {pic_url}")
            image_base64 = image_handler.get_image_base64_from_url(pic_url)
            download_duration = int((time.time() - download_start) * 1000)
            
            if performance_monitor and request_id:
                performance_monitor.track_bottleneck(
                    request_id, "image_handler", "download_image", download_duration
                )
            
            if not image_base64:
                return self.build_reply(from_user, to_user, "抱歉，图片下载失败，请重试。")
            
            print(f"图片下载完成，耗时 {download_duration}ms")
            
            if ENABLE_USER_MEMORY:
                user_memory.add_conversation(from_user, "user", "[发送了一张图片]")
                user_memory.increment_message_count(from_user)
            
            history_context = []
            if ENABLE_USER_MEMORY:
                history_context = user_memory.get_context_for_ai(from_user, max_messages=2)
            
            analysis_prompt = """请分析这张图片：

1. 如果是表情包/梗图：
   - 用幽默风趣的语气描述图片内容
   - 解释这个梗的含义和使用场景
   - 给出1-2个使用示例
   - 语气要轻松活泼，像和朋友聊天一样

2. 如果是普通照片：
   - 简单描述图片内容
   - 可以加点有趣的评论

注意：
- 直接面对用户说话
- 可以用表情符号😄
- 字数控制在150字左右"""
            
            print("正在分析图片...")
            ai_response = zhipu_client.get_response(
                user_message=analysis_prompt,
                user_id=from_user,
                history=history_context,
                image_base64=image_base64,
                request_id=request_id
            )
            
            if ai_response and ENABLE_CONTENT_FILTER:
                ai_response = content_filter.filter_ai_response(ai_response)
            
            if ai_response:
                print(f"✓ 图片分析完成: {ai_response[:50]}...")
                
                if ENABLE_USER_MEMORY:
                    user_memory.add_conversation(from_user, "assistant", ai_response)
                
                return self.build_reply(from_user, to_user, ai_response)
            else:
                return self.build_reply(from_user, to_user, "抱歉，图片分析失败，请稍后再试。")
                
        except Exception as e:
            print(f"处理图片消息异常: {e}")
            import traceback
            traceback.print_exc()
            return self.build_reply(from_user, to_user, "抱歉，处理图片时出现错误。")
    
    def handle_text_message(self, message: dict, request_id: str = None) -> str:
        """处理文本消息（带性能监控）"""
        from_user = message.get("from_user")
        to_user = message.get("to_user")
        user_input = message.get("content", "").strip()
        
        if not user_input:
            return self.build_reply(from_user, to_user, "请输入内容")
        
        # 检查是否有待处理的图片任务
        if ASYNC_ENABLED and async_task_manager:
            pending_task = self._check_pending_image_task(from_user)
            if pending_task:
                task_status = async_task_manager.get_task_status(pending_task)
                
                if task_status["status"] == "completed" and task_status.get("result"):
                    # 任务已完成，返回结果
                    result = task_status["result"]
                    if result.get("success"):
                        response = result.get("response", "分析完成，但没有结果。")
                        # 返回结果后，清理任务记录
                        return self.build_reply(from_user, to_user, 
                            f"📸 图片分析结果：\n\n{response}")
                    else:
                        return self.build_reply(from_user, to_user, 
                            f"❌ 图片分析失败：{result.get('error', '未知错误')}")
                
                elif task_status["status"] == "processing":
                    # 还在处理中
                    return self.build_reply(from_user, to_user, 
                        "⏳ 图片还在分析中，请再等几秒...")
                
                elif task_status["status"] == "pending":
                    # 在队列中等待
                    queue_size = async_task_manager.get_queue_size()
                    return self.build_reply(from_user, to_user, 
                        f"⏳ 图片在队列中等待处理（前面还有 {queue_size} 个任务）...")
        
        # 内容安全检查（记录性能）
        if ENABLE_CONTENT_FILTER:
            filter_start = time.time()
            is_safe, filtered_input = content_filter.filter_user_input(user_input)
            filter_duration = int((time.time() - filter_start) * 1000)
            
            if performance_monitor and request_id:
                performance_monitor.track_bottleneck(
                    request_id, "content_filter", "filter_input", filter_duration
                )
            
            if not is_safe:
                print(f"用户 {from_user[:10]}... 输入被拦截: {filtered_input}")
                return self.build_reply(from_user, to_user, "您的内容包含不安全信息，请修改后重试。")
            
            user_input = filtered_input
        
        # 更新用户记忆
        if ENABLE_USER_MEMORY:
            user_memory.add_conversation(from_user, "user", user_input)
            user_memory.increment_message_count(from_user)
        
        # 特殊命令处理
        if user_input == "/help":
            help_msg = """欢迎使用AI助手！🤖

📝 命令列表：
/help - 显示帮助
/about - 关于助手
/clear - 清除历史
/memory - 查看我的记忆
/stats - 查看统计
/perf - 查看性能统计

✨ 功能说明：
💬 发送文字 - 智能对话，记住上下文
📸 发送图片 - AI识别表情包和梗图
   （图片分析需要8-10秒，请耐心等待）

💡 小贴士：
发送图片后，等几秒再发送任意消息
即可获取分析结果！"""
            return self.build_reply(from_user, to_user, help_msg)
        
        if user_input == "/about":
            about_msg = """智谱AI微信助手 v3.5

✨ 功能特色：
• 智能对话（GPT-4级别）
• 图片理解（识别表情包）
• 上下文记忆
• 内容安全过滤
• 响应缓存加速
• 性能实时监控

技术支持：智谱AI GLM-4V"""
            return self.build_reply(from_user, to_user, about_msg)
        
        if user_input == "/clear" and ENABLE_USER_MEMORY:
            user_memory.clear_conversation_history(from_user)
            return self.build_reply(from_user, to_user, "对话历史已清除")
        
        if user_input == "/memory" and ENABLE_USER_MEMORY:
            profile = user_memory.get_user_profile(from_user)
            if profile:
                memory_info = f"""📊 你的使用统计

消息数: {profile['message_count']} 条
最后活跃: {profile['last_seen'].strftime('%Y-%m-%d %H:%M')}
注册时间: {profile['created_at'].strftime('%Y-%m-%d')}

发送 /clear 可清除历史"""
                return self.build_reply(from_user, to_user, memory_info)
        
        if user_input == "/stats":
            stats_msg = """📈 系统统计

✅ 功能状态：
• 智能对话 - 运行中
• 图片识别 - 支持
• 表情包解析 - 支持
• 上下文记忆 - 开启
• 缓存加速 - 开启
• 性能监控 - 开启

🎭 支持识别：
• 表情包/梗图
• 普通照片
• 截图/文字图片

💡 试试发送表情包，看看AI
会怎么回复你！😄"""
            return self.build_reply(from_user, to_user, stats_msg)
        
        if user_input == "/perf" and performance_monitor:
            stats = performance_monitor.get_statistics(hours=1)
            perf_msg = f"""⚡ 性能统计（最近1小时）

总请求: {stats.get('total_requests', 0)} 次
平均响应: {stats.get('avg_response_time_ms', 0)}ms
缓存命中率: {stats.get('cache_hit_rate', 0)}%
慢请求: {stats.get('slow_requests', 0)} 次
超时: {stats.get('timeout_requests', 0)} 次

响应时间：
最快: {stats.get('min_response_time_ms', 0)}ms
最慢: {stats.get('max_response_time_ms', 0)}ms"""
            return self.build_reply(from_user, to_user, perf_msg)
        
        print(f"📝 用户 {from_user[:10]}... 发送: {user_input[:50]}")
        
        # 获取对话上下文
        history_context = []
        if ENABLE_USER_MEMORY:
            history_context = user_memory.get_context_for_ai(from_user, max_messages=4)
        
        # 调用AI
        ai_response = zhipu_client.get_response(
            user_message=user_input,
            user_id=from_user,
            history=history_context,
            request_id=request_id
        )
        
        # 过滤AI回复
        if ai_response and ENABLE_CONTENT_FILTER:
            ai_response = content_filter.filter_ai_response(ai_response)
        
        if ai_response:
            print(f"✓ AI回复: {ai_response[:50]}...")
            
            # 记录AI回复
            if ENABLE_USER_MEMORY:
                user_memory.add_conversation(from_user, "assistant", ai_response)
            
            # 提取并存储记忆
            self._extract_and_store_memory(from_user, user_input, ai_response)
            
            return self.build_reply(from_user, to_user, ai_response)
        else:
            error_msg = "抱歉，AI服务暂时不可用，请稍后再试。"
            return self.build_reply(from_user, to_user, error_msg)
    
    def _extract_and_store_memory(self, user_id: str, user_input: str, ai_response: str):
        """从对话中提取并存储用户记忆"""
        if not ENABLE_USER_MEMORY:
            return
        
        name_keywords = ["我叫", "我是", "我的名字是"]
        for keyword in name_keywords:
            if keyword in user_input:
                start_idx = user_input.find(keyword) + len(keyword)
                name_part = user_input[start_idx:].strip()
                if len(name_part) > 0:
                    possible_name = name_part.split()[0][:10]
                    user_memory.set_memory(user_id, "fact", "name", possible_name)
                    print(f"✓ 记录用户 {user_id[:10]}... 的名字: {possible_name}")
                    break
    
    def _check_pending_image_task(self, user_id: str) -> str:
        """检查用户是否有待处理的图片任务"""
        if not ASYNC_ENABLED or not async_task_manager:
            return None
        
        # 查找该用户最近的图片任务
        user_prefix = f"image_{user_id}"
        for task_id in list(async_task_manager.tasks.keys()):
            if task_id.startswith(user_prefix):
                task = async_task_manager.tasks[task_id]
                # 只返回未完成或刚完成的任务（60秒内）
                if task["status"] in ["pending", "processing"]:
                    return task_id
                elif task["status"] == "completed":
                    # 如果是60秒内完成的，也返回
                    if time.time() - task.get("completed_at", 0) < 60:
                        return task_id
        
        return None


# 创建全局处理器实例
wechat_handler = WeChatHandler()
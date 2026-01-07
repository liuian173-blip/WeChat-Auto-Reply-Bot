"""
内容安全过滤器
"""

import re
import json
from typing import List, Tuple, Set
import os


class ContentFilter:
    def __init__(self, config_path: str = "data/filter_config.json"):
        """
        初始化内容过滤器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.sensitive_words = set()
        self.malicious_patterns = [
            r'<script.*?>.*?</script>',
            r'on\w+=".*?"',
            r'javascript:',
            r'vbscript:',
            r'eval\(',
            r'exec\(',
            r'alert\(',
            r'document\.',
            r'window\.',
            r'location\.'
        ]
        
        # 加载配置
        self.load_config()
    
    def load_config(self):
        """加载过滤配置"""
        default_config = {
            "sensitive_words": [
                # 政治敏感词
                "反动", "分裂", "颠覆",
                # 暴力恐怖
                "杀人", "爆炸", "恐怖",
                # 色情低俗
                "色情", "淫秽", "裸体",
                # 其他
                "诈骗", "赌博", "毒品"
            ],
            "max_length": 500,
            "enable_url_filter": True,
            "enable_emoji_filter": False
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.sensitive_words = set(config.get("sensitive_words", default_config["sensitive_words"]))
            else:
                # 创建默认配置
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=2)
                self.sensitive_words = set(default_config["sensitive_words"])
                
        except Exception as e:
            print(f"加载过滤配置失败: {e}")
            self.sensitive_words = set(default_config["sensitive_words"])
    
    def add_sensitive_word(self, word: str):
        """添加敏感词"""
        self.sensitive_words.add(word)
        self.save_config()
    
    def remove_sensitive_word(self, word: str):
        """移除敏感词"""
        self.sensitive_words.discard(word)
        self.save_config()
    
    def save_config(self):
        """保存配置"""
        try:
            config = {
                "sensitive_words": list(self.sensitive_words),
                "max_length": 500,
                "enable_url_filter": True,
                "enable_emoji_filter": False
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def check_text(self, text: str) -> Tuple[bool, str]:
        """
        检查文本安全性
        
        Returns:
            (是否安全, 错误消息)
        """
        if not text or not isinstance(text, str):
            return False, "内容为空"
        
        # 长度检查
        if len(text) > 500:
            return False, "内容过长（超过500字）"
        
        # 敏感词检查
        for word in self.sensitive_words:
            if word in text:
                return False, f"包含敏感词：{word}"
        
        # 恶意脚本检查
        for pattern in self.malicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "包含恶意代码"
        
        # URL检查
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, text)
        if urls and len(urls) > 3:  # 限制URL数量
            return False, "包含过多外部链接"
        
        # 特殊字符检查（防止注入）
        dangerous_chars = [';', '|', '&', '`', '$', '(', ')', '{', '}']
        char_count = sum(text.count(c) for c in dangerous_chars)
        if char_count > 10:
            return False, "包含过多特殊字符"
        
        return True, "安全"
    
    def sanitize_text(self, text: str) -> str:
        """
        净化文本，移除不安全内容
        
        Returns:
            净化后的文本
        """
        if not text:
            return ""
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除恶意脚本
        for pattern in self.malicious_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # 移除URL（可选，或替换为占位符）
        text = re.sub(r'https?://[^\s]+', '[链接]', text)
        
        # 过滤敏感词（替换为*）
        for word in self.sensitive_words:
            if word in text:
                text = text.replace(word, '*' * len(word))
        
        # 限制长度
        if len(text) > 480:
            text = text[:450] + "..."
        
        return text
    
    def filter_user_input(self, text: str) -> Tuple[bool, str]:
        """过滤用户输入"""
        is_safe, message = self.check_text(text)
        if not is_safe:
            return False, f"输入内容不安全：{message}"
        return True, self.sanitize_text(text)
    
    def filter_ai_response(self, text: str) -> str:
        """过滤AI回复"""
        return self.sanitize_text(text)
    
    def get_sensitive_words(self) -> List[str]:
        """获取敏感词列表"""
        return sorted(list(self.sensitive_words))


# 全局过滤器实例
content_filter = ContentFilter()
"""
用户记忆管理器 - 修复版
"""

import json
import time
import sqlite3
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta


class UserMemory:
    def __init__(self, db_path: str = "data/user_memory.db"):
        """
        初始化用户记忆管理器
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        # 用户信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                nickname TEXT,
                created_at INTEGER,
                last_seen INTEGER,
                message_count INTEGER DEFAULT 0,
                preferences TEXT DEFAULT '{}'
            )
        ''')
        
        # 对话历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT,
                content TEXT,
                timestamp INTEGER,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
            )
        ''')
        
        # 用户记忆表（结构化记忆）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                memory_type TEXT,
                key TEXT,
                value TEXT,
                confidence REAL DEFAULT 1.0,
                created_at INTEGER,
                updated_at INTEGER,
                FOREIGN KEY (user_id) REFERENCES user_profiles (user_id),
                UNIQUE(user_id, memory_type, key)
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_user ON conversation_history(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_time ON conversation_history(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_user ON user_memories(user_id)')
        
        self.conn.commit()
    
    # ========== 用户基本信息 ==========
    
    def create_or_update_user(self, user_id: str, nickname: str = None):
        """创建或更新用户信息"""
        cursor = self.conn.cursor()
        now = int(time.time())
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_profiles 
            (user_id, nickname, created_at, last_seen, message_count)
            VALUES (?, ?, COALESCE((SELECT created_at FROM user_profiles WHERE user_id = ?), ?), ?, 
                   COALESCE((SELECT message_count FROM user_profiles WHERE user_id = ?), 0))
        ''', (user_id, nickname, user_id, now, now, user_id))
        
        self.conn.commit()
    
    def update_last_seen(self, user_id: str):
        """更新最后活动时间"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE user_profiles SET last_seen = ? WHERE user_id = ?",
            (int(time.time()), user_id)
        )
        self.conn.commit()
    
    def increment_message_count(self, user_id: str):
        """增加消息计数"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE user_profiles SET message_count = message_count + 1 WHERE user_id = ?",
            (user_id,)
        )
        self.conn.commit()
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户档案"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT user_id, nickname, created_at, last_seen, message_count, preferences FROM user_profiles WHERE user_id = ?",
            (user_id,)
        )
        
        row = cursor.fetchone()
        if row:
            user_id, nickname, created_at, last_seen, message_count, preferences = row
            return {
                "user_id": user_id,
                "nickname": nickname,
                "created_at": datetime.fromtimestamp(created_at),
                "last_seen": datetime.fromtimestamp(last_seen),
                "message_count": message_count,
                "preferences": json.loads(preferences) if preferences else {}
            }
        return None
    
    # ========== 对话历史管理 ==========
    
    def add_conversation(self, user_id: str, role: str, content: str):
        """添加对话记录"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO conversation_history (user_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, role, content, int(time.time())))
        
        # 清理旧记录（保留最近20条）
        cursor.execute('''
            DELETE FROM conversation_history 
            WHERE user_id = ? AND id NOT IN (
                SELECT id FROM conversation_history 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 20
            )
        ''', (user_id, user_id))
        
        self.conn.commit()
    
    def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取对话历史"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT role, content, timestamp 
            FROM conversation_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        history = []
        for role, content, timestamp in cursor.fetchall():
            history.append({
                "role": role,
                "content": content,
                "time": datetime.fromtimestamp(timestamp)
            })
        
        # 按时间正序返回
        return list(reversed(history))
    
    def clear_conversation_history(self, user_id: str):
        """清空对话历史"""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM conversation_history WHERE user_id = ?",
            (user_id,)
        )
        self.conn.commit()
    
    # ========== 结构化记忆 ==========
    
    def set_memory(self, user_id: str, memory_type: str, key: str, value: Any, confidence: float = 1.0):
        """设置记忆"""
        cursor = self.conn.cursor()
        now = int(time.time())
        value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_memories 
            (user_id, memory_type, key, value, confidence, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM user_memories WHERE user_id = ? AND memory_type = ? AND key = ?), ?), ?)
        ''', (user_id, memory_type, key, value_str, confidence, user_id, memory_type, key, now, now))
        
        self.conn.commit()
    
    def get_memory(self, user_id: str, memory_type: str = None, key: str = None) -> Any:
        """获取记忆"""
        cursor = self.conn.cursor()
        
        if memory_type and key:
            cursor.execute(
                "SELECT value FROM user_memories WHERE user_id = ? AND memory_type = ? AND key = ?",
                (user_id, memory_type, key)
            )
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except:
                    return row[0]
        elif memory_type:
            cursor.execute(
                "SELECT key, value FROM user_memories WHERE user_id = ? AND memory_type = ?",
                (user_id, memory_type)
            )
            memories = {}
            for key, value in cursor.fetchall():
                try:
                    memories[key] = json.loads(value)
                except:
                    memories[key] = value
            return memories
        else:
            cursor.execute(
                "SELECT memory_type, key, value FROM user_memories WHERE user_id = ?",
                (user_id,)
            )
            all_memories = {}
            for memory_type, key, value in cursor.fetchall():
                if memory_type not in all_memories:
                    all_memories[memory_type] = {}
                try:
                    all_memories[memory_type][key] = json.loads(value)
                except:
                    all_memories[memory_type][key] = value
            return all_memories
        
        return None
    
    def delete_memory(self, user_id: str, memory_type: str = None, key: str = None):
        """删除记忆"""
        cursor = self.conn.cursor()
        
        if memory_type and key:
            cursor.execute(
                "DELETE FROM user_memories WHERE user_id = ? AND memory_type = ? AND key = ?",
                (user_id, memory_type, key)
            )
        elif memory_type:
            cursor.execute(
                "DELETE FROM user_memories WHERE user_id = ? AND memory_type = ?",
                (user_id, memory_type)
            )
        else:
            cursor.execute(
                "DELETE FROM user_memories WHERE user_id = ?",
                (user_id,)
            )
        
        self.conn.commit()
    
    # ========== 记忆提取和总结 ==========
    
    def extract_user_info(self, user_id: str) -> Dict[str, Any]:
        """从对话历史中提取用户信息"""
        history = self.get_conversation_history(user_id, limit=20)
        
        # 统计关键词
        from collections import Counter
        all_text = " ".join([h["content"] for h in history if h["role"] == "user"])
        words = all_text.split()
        
        return {
            "top_keywords": Counter(words).most_common(10),
            "conversation_count": len([h for h in history if h["role"] == "user"]),
            "avg_message_length": sum(len(h["content"]) for h in history) / max(len(history), 1)
        }
    
    def get_context_for_ai(self, user_id: str, max_messages: int = 6) -> List[Dict[str, str]]:
        """为AI生成对话上下文"""
        history = self.get_conversation_history(user_id, limit=max_messages * 2)
        
        # 转换为AI需要的格式
        context = []
        for item in history[-max_messages:]:
            context.append({
                "role": item["role"],
                "content": item["content"]
            })
        
        # 添加用户记忆作为系统提示
        user_memories = self.get_memory(user_id)
        if user_memories:
            memory_text = "用户相关信息："
            for mem_type, mem_data in user_memories.items():
                if isinstance(mem_data, dict):
                    for key, value in mem_data.items():
                        memory_text += f"\n- {key}: {value}"
            
            if memory_text != "用户相关信息：":
                context.insert(0, {
                    "role": "system",
                    "content": memory_text
                })
        
        return context
    
    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        cursor = self.conn.cursor()
        cutoff_time = int(time.time()) - (days * 24 * 3600)
        
        # 清理旧对话历史
        cursor.execute(
            "DELETE FROM conversation_history WHERE timestamp < ?",
            (cutoff_time,)
        )
        
        # 清理长时间不活跃的用户
        cursor.execute('''
            DELETE FROM user_profiles 
            WHERE last_seen < ? AND message_count < 10
        ''', (cutoff_time,))
        
        self.conn.commit()
        return cursor.rowcount


# 全局用户记忆实例
user_memory = UserMemory()
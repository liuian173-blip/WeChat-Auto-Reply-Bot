"""
简化版缓存管理器 - 适用于短期运行的微信公众号
"""

import json
import hashlib
import time
import sqlite3
import os
from typing import Optional, Dict, Any


class SimpleCacheManager:
    def __init__(self, ttl: int = 7200, max_size: int = 500):
        """
        简化版缓存管理器
        
        Args:
            ttl: 缓存过期时间（秒），默认2小时
            max_size: 最大缓存条目数
        """
        self.ttl = ttl
        self.max_size = max_size
        
        # 内存缓存（主缓存）
        self.memory_cache = {}
        
        # SQLite持久化（统一使用 cache.db）
        self.use_sqlite = True
        if self.use_sqlite:
            self.init_sqlite()
        
        print(f"缓存管理器初始化: TTL={ttl//60}分钟, 最大{max_size}条")
    
    def init_sqlite(self):
        """初始化SQLite"""
        os.makedirs("data", exist_ok=True)
        # 统一使用 cache.db
        self.conn = sqlite3.connect("data/cache.db", check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT,
                created_at INTEGER,
                expire_at INTEGER
            )
        ''')
        self.conn.commit()
    
    def generate_key(self, query: str, user_id: Optional[str] = None) -> str:
        """生成缓存键"""
        content = f"{user_id}:{query}" if user_id else query
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        # 优先从内存缓存获取
        if key in self.memory_cache:
            item = self.memory_cache[key]
            if time.time() < item["expire_at"]:
                return item["value"]
            else:
                # 过期，从内存中删除
                del self.memory_cache[key]
        
        # 如果启用SQLite，尝试从数据库获取
        if self.use_sqlite and hasattr(self, 'conn'):
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT value, expire_at FROM cache WHERE key = ?", (key,))
                row = cursor.fetchone()
                
                if row:
                    value_str, expire_at = row
                    if time.time() < expire_at:
                        try:
                            value = json.loads(value_str)
                        except:
                            value = value_str
                        
                        # 存入内存缓存
                        self.memory_cache[key] = {
                            "value": value,
                            "expire_at": expire_at
                        }
                        return value
                    else:
                        # 过期，从数据库删除
                        cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
                        self.conn.commit()
            except Exception as e:
                print(f"从数据库读取缓存失败: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        expire_at = time.time() + (ttl or self.ttl)
        
        # 存入内存缓存
        self.memory_cache[key] = {
            "value": value,
            "expire_at": expire_at,
            "created_at": time.time()
        }
        
        # 如果缓存已满，删除最旧的条目
        if len(self.memory_cache) > self.max_size:
            oldest_key = min(self.memory_cache.keys(), 
                           key=lambda k: self.memory_cache[k]["created_at"])
            del self.memory_cache[oldest_key]
        
        # 如果启用SQLite，也存入数据库
        if self.use_sqlite and hasattr(self, 'conn'):
            try:
                value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO cache (key, value, created_at, expire_at)
                    VALUES (?, ?, ?, ?)
                ''', (key, value_str, int(time.time()), int(expire_at)))
                self.conn.commit()
            except Exception as e:
                print(f"保存缓存到数据库失败: {e}")
    
    def delete(self, key: str):
        """删除缓存"""
        self.memory_cache.pop(key, None)
        
        if self.use_sqlite and hasattr(self, 'conn'):
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
                self.conn.commit()
            except Exception as e:
                print(f"从数据库删除缓存失败: {e}")
    
    def clear(self):
        """清空所有缓存"""
        self.memory_cache.clear()
        
        if self.use_sqlite and hasattr(self, 'conn'):
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM cache")
                self.conn.commit()
            except Exception as e:
                print(f"清空数据库缓存失败: {e}")
    
    def cleanup_expired(self) -> int:
        """清理过期缓存"""
        now = time.time()
        expired_keys = []
        
        # 清理内存缓存
        for key, item in list(self.memory_cache.items()):
            if now >= item["expire_at"]:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        # 清理数据库缓存
        db_expired = 0
        if self.use_sqlite and hasattr(self, 'conn'):
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM cache WHERE expire_at < ?", (now,))
                db_expired = cursor.rowcount
                self.conn.commit()
            except Exception as e:
                print(f"清理数据库缓存失败: {e}")
        
        total_expired = len(expired_keys) + db_expired
        if total_expired > 0:
            print(f"清理了 {total_expired} 条过期缓存")
        
        return total_expired
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            "memory_size": len(self.memory_cache),
            "max_size": self.max_size,
            "ttl_minutes": self.ttl // 60
        }
        
        if self.use_sqlite and hasattr(self, 'conn'):
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM cache")
                stats["db_size"] = cursor.fetchone()[0]
            except Exception as e:
                print(f"获取数据库统计失败: {e}")
                stats["db_size"] = 0
        
        return stats


# 全局缓存实例
cache_manager = SimpleCacheManager(ttl=7200, max_size=500)


# 装饰器：自动缓存函数返回值
def cache_response(ttl: int = 7200):
    """
    缓存装饰器
    
    用法：
    @cache_response(ttl=3600)
    def my_function(arg1, arg2):
        return result
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # 生成缓存键
            import hashlib
            cache_key = hashlib.md5(
                f"{func.__name__}:{str(args)}:{str(kwargs)}".encode()
            ).hexdigest()
            
            # 尝试从缓存获取
            cached = cache_manager.get(cache_key)
            if cached is not None:
                return cached
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 保存到缓存
            if result is not None:
                cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


# 确保所有需要的内容都被导出
__all__ = ['cache_manager', 'SimpleCacheManager', 'cache_response']
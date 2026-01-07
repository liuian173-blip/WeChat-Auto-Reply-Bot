"""
基于使用时长的自动清理器
适用于短期运行的微信公众号应用
支持图片清理
"""

import time
import threading
import sqlite3
import os
import glob
from datetime import datetime, timedelta


class AutoCleaner:
    def __init__(self, cleanup_interval: int = 1800, max_duration: int = 3600):
        """
        初始化自动清理器
        
        Args:
            cleanup_interval: 清理间隔（秒），默认30分钟
            max_duration: 最大运行时长（秒），默认1小时
        """
        self.cleanup_interval = cleanup_interval
        self.max_duration = max_duration
        self.start_time = time.time()
        self.running = False
        self.thread = None
        
        # 创建数据目录
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/images", exist_ok=True)
        
        # 初始化数据库
        self.init_database()
        
        print(f"自动清理器初始化完成:")
        print(f"- 清理间隔: {cleanup_interval//60}分钟")
        print(f"- 最大运行时长: {max_duration//60}分钟")
        print(f"- 缓存过期时间: {7200//60}分钟")
    
    def init_database(self):
        """初始化清理记录数据库"""
        self.conn = sqlite3.connect("data/auto_cleanup.db", check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cleanup_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                items_cleaned INTEGER,
                execution_time INTEGER,
                duration_ms INTEGER,
                timestamp INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS session_info (
                session_id TEXT PRIMARY KEY,
                start_time INTEGER,
                last_cleanup INTEGER,
                total_cleanups INTEGER DEFAULT 0
            )
        ''')
        
        self.conn.commit()
        
        # 记录当前会话
        session_id = f"session_{int(time.time())}"
        cursor.execute('''
            INSERT OR REPLACE INTO session_info 
            (session_id, start_time, last_cleanup, total_cleanups)
            VALUES (?, ?, ?, ?)
        ''', (session_id, int(time.time()), int(time.time()), 0))
        self.conn.commit()
    
    def log_cleanup(self, action: str, items_cleaned: int, duration_ms: int):
        """记录清理日志"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO cleanup_logs 
            (action, items_cleaned, execution_time, duration_ms, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (action, items_cleaned, int(time.time()), duration_ms, int(time.time())))
        self.conn.commit()
    
    def update_session_info(self):
        """更新会话信息"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE session_info 
            SET last_cleanup = ?, total_cleanups = total_cleanups + 1
            WHERE session_id = (SELECT session_id FROM session_info ORDER BY start_time DESC LIMIT 1)
        ''', (int(time.time()),))
        self.conn.commit()
    
    def cleanup_expired_cache(self) -> int:
        """清理过期缓存（2小时以上）"""
        try:
            start_time = time.time()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 清理过期缓存...")
            
            cleaned = 0
            db_path = "data/cache.db"
            
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 删除2小时前的缓存
                cutoff_time = int(time.time()) - 7200  # 2小时
                cursor.execute("DELETE FROM cache WHERE expire_at < ?", (cutoff_time,))
                cleaned = cursor.rowcount
                conn.commit()
                
                # 关闭连接
                conn.close()
                
                # 重新连接并执行VACUUM（在自动提交模式下）
                if cleaned > 0:  # 只有删除了数据才需要VACUUM
                    conn = sqlite3.connect(db_path)
                    conn.isolation_level = None  # 设置为自动提交模式
                    cursor = conn.cursor()
                    cursor.execute("VACUUM")
                    conn.close()
            
            duration = int((time.time() - start_time) * 1000)
            self.log_cleanup("expired_cache", cleaned, duration)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 清理了 {cleaned} 条过期缓存，耗时 {duration}ms")
            return cleaned
            
        except Exception as e:
            print(f"清理缓存失败: {e}")
            return 0
    
    def cleanup_temp_files(self) -> int:
        """清理临时文件"""
        try:
            start_time = time.time()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 清理临时文件...")
            
            cleaned = 0
            
            # 清理常见的临时文件
            temp_patterns = ["*.tmp", "*.temp", "~*", "*.log"]
            
            for pattern in temp_patterns:
                for filepath in glob.glob(pattern):
                    try:
                        os.remove(filepath)
                        cleaned += 1
                    except:
                        pass
            
            duration = int((time.time() - start_time) * 1000)
            self.log_cleanup("temp_files", cleaned, duration)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 清理了 {cleaned} 个临时文件，耗时 {duration}ms")
            return cleaned
            
        except Exception as e:
            print(f"清理临时文件失败: {e}")
            return 0
    
    def cleanup_old_images(self) -> int:
        """清理旧图片（24小时前）"""
        try:
            start_time = time.time()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 清理旧图片...")
            
            cleaned = 0
            image_dir = "data/images"
            
            if os.path.exists(image_dir):
                cutoff_time = time.time() - 86400  # 24小时
                
                for filename in os.listdir(image_dir):
                    filepath = os.path.join(image_dir, filename)
                    
                    try:
                        if os.path.isfile(filepath):
                            # 检查文件修改时间
                            if os.path.getmtime(filepath) < cutoff_time:
                                os.remove(filepath)
                                cleaned += 1
                    except Exception as e:
                        print(f"删除图片失败 {filepath}: {e}")
            
            duration = int((time.time() - start_time) * 1000)
            self.log_cleanup("old_images", cleaned, duration)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 清理了 {cleaned} 张旧图片，耗时 {duration}ms")
            return cleaned
            
        except Exception as e:
            print(f"清理图片失败: {e}")
            return 0
    
    def cleanup_old_session_data(self) -> int:
        """清理旧的会话数据（24小时前）"""
        try:
            start_time = time.time()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 清理旧会话数据...")
            
            cleaned = 0
            cutoff_time = int(time.time()) - 86400  # 24小时
            
            # 清理旧的会话记录
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM session_info WHERE start_time < ?", (cutoff_time,))
            cleaned += cursor.rowcount
            
            # 清理旧的清理日志
            cursor.execute("DELETE FROM cleanup_logs WHERE timestamp < ?", (cutoff_time,))
            cleaned += cursor.rowcount
            
            self.conn.commit()
            
            duration = int((time.time() - start_time) * 1000)
            self.log_cleanup("old_sessions", cleaned, duration)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 清理了 {cleaned} 条旧会话数据，耗时 {duration}ms")
            return cleaned
            
        except Exception as e:
            print(f"清理旧会话数据失败: {e}")
            return 0
    
    def cleanup_user_memory(self) -> int:
        """清理用户记忆数据库中的旧数据"""
        try:
            start_time = time.time()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 清理用户记忆旧数据...")
            
            cleaned = 0
            db_path = "data/user_memory.db"
            
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # 清理30天前的对话历史
                cutoff_time = int(time.time()) - (30 * 24 * 3600)
                cursor.execute("DELETE FROM conversation_history WHERE timestamp < ?", (cutoff_time,))
                cleaned += cursor.rowcount
                
                # 清理长时间不活跃的用户（30天未活动且消息少于10条）
                cursor.execute('''
                    DELETE FROM user_profiles 
                    WHERE last_seen < ? AND message_count < 10
                ''', (cutoff_time,))
                cleaned += cursor.rowcount
                
                # 提交并关闭
                conn.commit()
                conn.close()
                
                # 重新连接并执行VACUUM（在自动提交模式下）
                if cleaned > 0:  # 只有删除了数据才需要VACUUM
                    conn = sqlite3.connect(db_path)
                    conn.isolation_level = None  # 设置为自动提交模式
                    cursor = conn.cursor()
                    cursor.execute("VACUUM")
                    conn.close()
            
            duration = int((time.time() - start_time) * 1000)
            self.log_cleanup("user_memory", cleaned, duration)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 清理了 {cleaned} 条用户记忆数据，耗时 {duration}ms")
            return cleaned
            
        except Exception as e:
            print(f"清理用户记忆失败: {e}")
            return 0
    
    def run_all_cleanup(self) -> dict:
        """运行所有清理任务"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始全面清理...")
        
        results = {
            "expired_cache": self.cleanup_expired_cache(),
            "temp_files": self.cleanup_temp_files(),
            "old_images": self.cleanup_old_images(),
            "old_sessions": self.cleanup_old_session_data(),
            "user_memory": self.cleanup_user_memory()
        }
        
        self.update_session_info()
        
        total_cleaned = sum(results.values())
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 全面清理完成，共清理 {total_cleaned} 项")
        
        return results
    
    def should_stop(self) -> bool:
        """检查是否应该停止（达到最大运行时长）"""
        elapsed = time.time() - self.start_time
        return elapsed >= self.max_duration
    
    def run_cleanup_loop(self):
        """运行清理循环"""
        self.running = True
        print(f"自动清理器已启动，将每{self.cleanup_interval//60}分钟清理一次")
        
        try:
            while self.running:
                # 运行清理任务
                self.run_all_cleanup()
                
                # 检查是否应该停止
                if self.should_stop():
                    print(f"已达到最大运行时长{self.max_duration//60}分钟，停止清理器")
                    break
                
                # 等待下一次清理
                for _ in range(self.cleanup_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            print("清理器被中断")
        except Exception as e:
            print(f"清理器运行异常: {e}")
        finally:
            self.stop()
    
    def start(self):
        """启动清理器（在后台线程中）"""
        if not self.running:
            self.thread = threading.Thread(target=self.run_cleanup_loop, daemon=True)
            self.thread.start()
            print("自动清理器已在后台启动")
    
    def stop(self):
        """停止清理器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("自动清理器已停止")
    
    def run_once(self):
        """立即运行一次清理"""
        return self.run_all_cleanup()
    
    def get_status(self) -> dict:
        """获取状态信息"""
        elapsed = time.time() - self.start_time
        remaining = max(0, self.max_duration - elapsed)
        
        # 获取清理统计
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cleanup_logs")
        total_cleanups = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(items_cleaned) FROM cleanup_logs")
        total_items = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT total_cleanups FROM session_info ORDER BY start_time DESC LIMIT 1")
        session_cleanups = cursor.fetchone()
        session_cleanups = session_cleanups[0] if session_cleanups else 0
        
        # 获取各类统计
        cursor.execute("""
            SELECT action, SUM(items_cleaned) as total 
            FROM cleanup_logs 
            GROUP BY action
        """)
        cleanup_breakdown = dict(cursor.fetchall())
        
        return {
            "running": self.running,
            "elapsed_minutes": int(elapsed // 60),
            "remaining_minutes": int(remaining // 60),
            "total_cleanups": total_cleanups,
            "total_items_cleaned": total_items,
            "session_cleanups": session_cleanups,
            "next_cleanup_in": int(self.cleanup_interval - (elapsed % self.cleanup_interval)),
            "cleanup_breakdown": cleanup_breakdown
        }
    
    def get_cleanup_history(self, limit: int = 10) -> list:
        """获取清理历史记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT action, items_cleaned, duration_ms, timestamp
            FROM cleanup_logs
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        history = []
        for action, items, duration, timestamp in cursor.fetchall():
            history.append({
                "action": action,
                "items_cleaned": items,
                "duration_ms": duration,
                "timestamp": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        return history


# 全局清理器实例
auto_cleaner = AutoCleaner()
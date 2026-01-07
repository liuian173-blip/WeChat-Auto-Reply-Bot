"""
性能监控模块 - 监控和优化响应时间
"""

import time
import sqlite3
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import contextmanager
import threading


class PerformanceMonitor:
    def __init__(self, db_path: str = "data/performance.db"):
        """
        初始化性能监控器
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self.max_response_time = 4.5  # 最大响应时间（秒）
        self.warning_threshold = 4.0   # 警告阈值（秒）
        
        # 当前监控的请求
        self.active_requests = {}
        self.lock = threading.Lock()
        
        # 初始化数据库
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()
        
        print(f"性能监控器初始化完成")
        print(f"- 最大响应时间: {self.max_response_time}秒")
        print(f"- 警告阈值: {self.warning_threshold}秒")
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        # 响应时间记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS response_times (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_type TEXT,
                user_id TEXT,
                start_time REAL,
                end_time REAL,
                duration_ms INTEGER,
                status TEXT,
                has_cache INTEGER,
                has_image INTEGER,
                error_message TEXT,
                timestamp INTEGER
            )
        ''')
        
        # 瓶颈分析表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bottlenecks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component TEXT,
                operation TEXT,
                duration_ms INTEGER,
                request_id INTEGER,
                timestamp INTEGER,
                FOREIGN KEY (request_id) REFERENCES response_times(id)
            )
        ''')
        
        # 性能统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_type TEXT,
                avg_time REAL,
                min_time REAL,
                max_time REAL,
                total_requests INTEGER,
                slow_requests INTEGER,
                timeout_requests INTEGER,
                timestamp INTEGER
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_response_type ON response_times(request_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_response_time ON response_times(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_bottleneck_component ON bottlenecks(component)')
        
        conn.commit()
        conn.close()
    
    @contextmanager
    def track_request(self, request_type: str, user_id: str = None, has_image: bool = False):
        """
        跟踪请求性能的上下文管理器
        
        用法:
        with performance_monitor.track_request("text_message", user_id="123"):
            # 处理请求的代码
            pass
        """
        request_id = f"{request_type}_{int(time.time() * 1000)}"
        start_time = time.time()
        
        # 记录开始
        with self.lock:
            self.active_requests[request_id] = {
                "type": request_type,
                "user_id": user_id,
                "start_time": start_time,
                "has_image": has_image,
                "bottlenecks": []
            }
        
        status = "success"
        error_message = None
        has_cache = False
        
        try:
            yield {
                "request_id": request_id,
                "monitor": self
            }
        except Exception as e:
            status = "error"
            error_message = str(e)
            raise
        finally:
            end_time = time.time()
            duration_ms = int((end_time - start_time) * 1000)
            
            # 检查是否超时
            if duration_ms / 1000 > self.max_response_time:
                status = "timeout"
                print(f"⚠️ 请求超时: {request_type}, 耗时 {duration_ms}ms")
            elif duration_ms / 1000 > self.warning_threshold:
                print(f"⚠️ 响应较慢: {request_type}, 耗时 {duration_ms}ms")
            
            # 获取请求信息
            with self.lock:
                request_info = self.active_requests.pop(request_id, {})
                has_cache = request_info.get("has_cache", False)
                bottlenecks = request_info.get("bottlenecks", [])
            
            # 记录到数据库
            self._log_response_time(
                request_type=request_type,
                user_id=user_id,
                start_time=start_time,
                end_time=end_time,
                duration_ms=duration_ms,
                status=status,
                has_cache=has_cache,
                has_image=has_image,
                error_message=error_message,
                bottlenecks=bottlenecks
            )
    
    def mark_cache_hit(self, request_id: str):
        """标记缓存命中"""
        with self.lock:
            if request_id in self.active_requests:
                self.active_requests[request_id]["has_cache"] = True
    
    def track_bottleneck(self, request_id: str, component: str, operation: str, duration_ms: int):
        """
        记录性能瓶颈
        
        Args:
            request_id: 请求ID
            component: 组件名称（如 "ai_client", "cache", "image_handler"）
            operation: 操作名称（如 "api_call", "cache_get", "image_download"）
            duration_ms: 耗时（毫秒）
        """
        with self.lock:
            if request_id in self.active_requests:
                self.active_requests[request_id]["bottlenecks"].append({
                    "component": component,
                    "operation": operation,
                    "duration_ms": duration_ms,
                    "timestamp": int(time.time())
                })
    
    def _log_response_time(self, **kwargs):
        """记录响应时间到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 记录响应时间
            cursor.execute('''
                INSERT INTO response_times 
                (request_type, user_id, start_time, end_time, duration_ms, status, 
                 has_cache, has_image, error_message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                kwargs['request_type'],
                kwargs['user_id'],
                kwargs['start_time'],
                kwargs['end_time'],
                kwargs['duration_ms'],
                kwargs['status'],
                int(kwargs.get('has_cache', False)),
                int(kwargs.get('has_image', False)),
                kwargs.get('error_message'),
                int(time.time())
            ))
            
            request_db_id = cursor.lastrowid
            
            # 记录瓶颈
            bottlenecks = kwargs.get('bottlenecks', [])
            for bn in bottlenecks:
                cursor.execute('''
                    INSERT INTO bottlenecks 
                    (component, operation, duration_ms, request_id, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    bn['component'],
                    bn['operation'],
                    bn['duration_ms'],
                    request_db_id,
                    bn['timestamp']
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"记录性能数据失败: {e}")
    
    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取性能统计
        
        Args:
            hours: 统计时间范围（小时）
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = int(time.time()) - (hours * 3600)
            
            # 总体统计
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    AVG(duration_ms) as avg_time,
                    MIN(duration_ms) as min_time,
                    MAX(duration_ms) as max_time,
                    SUM(CASE WHEN duration_ms > ? THEN 1 ELSE 0 END) as slow_requests,
                    SUM(CASE WHEN status = 'timeout' THEN 1 ELSE 0 END) as timeouts,
                    SUM(CASE WHEN has_cache = 1 THEN 1 ELSE 0 END) as cache_hits
                FROM response_times
                WHERE timestamp > ?
            ''', (self.warning_threshold * 1000, cutoff_time))
            
            row = cursor.fetchone()
            total, avg_time, min_time, max_time, slow_requests, timeouts, cache_hits = row
            
            # 按类型统计
            cursor.execute('''
                SELECT 
                    request_type,
                    COUNT(*) as count,
                    AVG(duration_ms) as avg_time,
                    MAX(duration_ms) as max_time
                FROM response_times
                WHERE timestamp > ?
                GROUP BY request_type
            ''', (cutoff_time,))
            
            by_type = {}
            for request_type, count, avg, max_t in cursor.fetchall():
                by_type[request_type] = {
                    "count": count,
                    "avg_time_ms": round(avg, 2) if avg else 0,
                    "max_time_ms": max_t or 0
                }
            
            # 瓶颈分析
            cursor.execute('''
                SELECT 
                    component,
                    AVG(duration_ms) as avg_time,
                    COUNT(*) as count
                FROM bottlenecks
                WHERE timestamp > ?
                GROUP BY component
                ORDER BY avg_time DESC
                LIMIT 5
            ''', (cutoff_time,))
            
            bottlenecks = []
            for component, avg_time, count in cursor.fetchall():
                bottlenecks.append({
                    "component": component,
                    "avg_time_ms": round(avg_time, 2),
                    "count": count
                })
            
            conn.close()
            
            return {
                "total_requests": total or 0,
                "avg_response_time_ms": round(avg_time, 2) if avg_time else 0,
                "min_response_time_ms": min_time or 0,
                "max_response_time_ms": max_time or 0,
                "slow_requests": slow_requests or 0,
                "timeout_requests": timeouts or 0,
                "cache_hit_rate": round((cache_hits / total * 100), 2) if total > 0 else 0,
                "by_type": by_type,
                "top_bottlenecks": bottlenecks,
                "time_range_hours": hours
            }
            
        except Exception as e:
            print(f"获取统计数据失败: {e}")
            return {}
    
    def get_slow_requests(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最慢的请求"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    request_type,
                    user_id,
                    duration_ms,
                    has_cache,
                    has_image,
                    status,
                    timestamp
                FROM response_times
                ORDER BY duration_ms DESC
                LIMIT ?
            ''', (limit,))
            
            slow_requests = []
            for row in cursor.fetchall():
                req_type, user_id, duration, has_cache, has_image, status, ts = row
                slow_requests.append({
                    "type": req_type,
                    "user_id": user_id[:10] + "..." if user_id else "N/A",
                    "duration_ms": duration,
                    "has_cache": bool(has_cache),
                    "has_image": bool(has_image),
                    "status": status,
                    "time": datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                })
            
            conn.close()
            return slow_requests
            
        except Exception as e:
            print(f"获取慢请求失败: {e}")
            return []
    
    def get_bottleneck_details(self, component: str = None) -> List[Dict[str, Any]]:
        """获取瓶颈详情"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if component:
                cursor.execute('''
                    SELECT 
                        operation,
                        AVG(duration_ms) as avg_time,
                        MAX(duration_ms) as max_time,
                        COUNT(*) as count
                    FROM bottlenecks
                    WHERE component = ?
                    GROUP BY operation
                    ORDER BY avg_time DESC
                ''', (component,))
            else:
                cursor.execute('''
                    SELECT 
                        component,
                        operation,
                        AVG(duration_ms) as avg_time,
                        MAX(duration_ms) as max_time,
                        COUNT(*) as count
                    FROM bottlenecks
                    GROUP BY component, operation
                    ORDER BY avg_time DESC
                    LIMIT 20
                ''')
            
            details = []
            for row in cursor.fetchall():
                if component:
                    operation, avg_time, max_time, count = row
                    details.append({
                        "component": component,
                        "operation": operation,
                        "avg_time_ms": round(avg_time, 2),
                        "max_time_ms": max_time,
                        "count": count
                    })
                else:
                    comp, operation, avg_time, max_time, count = row
                    details.append({
                        "component": comp,
                        "operation": operation,
                        "avg_time_ms": round(avg_time, 2),
                        "max_time_ms": max_time,
                        "count": count
                    })
            
            conn.close()
            return details
            
        except Exception as e:
            print(f"获取瓶颈详情失败: {e}")
            return []
    
    def cleanup_old_data(self, days: int = 7):
        """清理旧数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = int(time.time()) - (days * 24 * 3600)
            
            # 清理旧的响应时间记录
            cursor.execute("DELETE FROM response_times WHERE timestamp < ?", (cutoff_time,))
            cleaned_responses = cursor.rowcount
            
            # 清理旧的瓶颈记录
            cursor.execute("DELETE FROM bottlenecks WHERE timestamp < ?", (cutoff_time,))
            cleaned_bottlenecks = cursor.rowcount
            
            # 优化数据库
            cursor.execute("VACUUM")
            
            conn.commit()
            conn.close()
            
            print(f"清理了 {cleaned_responses} 条响应记录，{cleaned_bottlenecks} 条瓶颈记录")
            return cleaned_responses + cleaned_bottlenecks
            
        except Exception as e:
            print(f"清理性能数据失败: {e}")
            return 0


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()
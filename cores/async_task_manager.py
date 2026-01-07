"""
异步任务管理器 - 处理耗时的AI请求
"""

import threading
import queue
import time
from typing import Dict, Any, Callable
from datetime import datetime


class AsyncTaskManager:
    def __init__(self, max_workers: int = 3):
        """
        初始化异步任务管理器
        
        Args:
            max_workers: 最大并发工作线程数
        """
        self.task_queue = queue.Queue()
        self.workers = []
        self.max_workers = max_workers
        self.running = False
        self.tasks = {}  # 存储任务状态
        
        print(f"异步任务管理器初始化: {max_workers} 个工作线程")
    
    def start(self):
        """启动工作线程"""
        if self.running:
            return
        
        self.running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True, name=f"Worker-{i+1}")
            worker.start()
            self.workers.append(worker)
        
        print(f"✓ 异步任务管理器已启动 ({self.max_workers} 个工作线程)")
    
    def stop(self):
        """停止所有工作线程"""
        self.running = False
        for _ in range(self.max_workers):
            self.task_queue.put(None)  # 发送停止信号
        
        for worker in self.workers:
            worker.join(timeout=2)
        
        print("异步任务管理器已停止")
    
    def add_task(self, task_id: str, task_func: Callable, *args, **kwargs):
        """
        添加异步任务
        
        Args:
            task_id: 任务唯一标识
            task_func: 要执行的函数
            *args, **kwargs: 函数参数
        """
        task = {
            "id": task_id,
            "func": task_func,
            "args": args,
            "kwargs": kwargs,
            "status": "pending",
            "created_at": time.time(),
            "result": None,
            "error": None
        }
        
        self.tasks[task_id] = task
        self.task_queue.put(task)
        
        print(f"✓ 任务已加入队列: {task_id}")
    
    def _worker(self):
        """工作线程 - 从队列中取任务执行"""
        thread_name = threading.current_thread().name
        print(f"工作线程 {thread_name} 已启动")
        
        while self.running:
            try:
                # 从队列获取任务（阻塞等待）
                task = self.task_queue.get(timeout=1)
                
                if task is None:  # 停止信号
                    break
                
                task_id = task["id"]
                print(f"[{thread_name}] 开始处理任务: {task_id}")
                
                # 更新任务状态
                self.tasks[task_id]["status"] = "processing"
                self.tasks[task_id]["started_at"] = time.time()
                
                try:
                    # 执行任务
                    result = task["func"](*task["args"], **task["kwargs"])
                    
                    # 记录结果
                    self.tasks[task_id]["status"] = "completed"
                    self.tasks[task_id]["result"] = result
                    self.tasks[task_id]["completed_at"] = time.time()
                    
                    duration = self.tasks[task_id]["completed_at"] - self.tasks[task_id]["started_at"]
                    print(f"[{thread_name}] ✓ 任务完成: {task_id} (耗时: {duration:.2f}秒)")
                    
                except Exception as e:
                    # 记录错误
                    self.tasks[task_id]["status"] = "failed"
                    self.tasks[task_id]["error"] = str(e)
                    self.tasks[task_id]["completed_at"] = time.time()
                    
                    print(f"[{thread_name}] ✗ 任务失败: {task_id} - {e}")
                
                finally:
                    self.task_queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[{thread_name}] 工作线程异常: {e}")
        
        print(f"工作线程 {thread_name} 已停止")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态字典
        """
        return self.tasks.get(task_id, {"status": "not_found"})
    
    def get_queue_size(self) -> int:
        """获取队列中等待的任务数量"""
        return self.task_queue.qsize()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_tasks = len(self.tasks)
        pending = sum(1 for t in self.tasks.values() if t["status"] == "pending")
        processing = sum(1 for t in self.tasks.values() if t["status"] == "processing")
        completed = sum(1 for t in self.tasks.values() if t["status"] == "completed")
        failed = sum(1 for t in self.tasks.values() if t["status"] == "failed")
        
        return {
            "total_tasks": total_tasks,
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "queue_size": self.get_queue_size(),
            "workers": self.max_workers
        }
    
    def cleanup_old_tasks(self, max_age_seconds: int = 3600):
        """清理旧任务记录（默认保留1小时）"""
        now = time.time()
        cleaned = 0
        
        for task_id in list(self.tasks.keys()):
            task = self.tasks[task_id]
            if "completed_at" in task:
                age = now - task["completed_at"]
                if age > max_age_seconds:
                    del self.tasks[task_id]
                    cleaned += 1
        
        if cleaned > 0:
            print(f"清理了 {cleaned} 个旧任务记录")
        
        return cleaned


# 全局任务管理器实例
async_task_manager = AsyncTaskManager(max_workers=3)
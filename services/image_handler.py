"""
图片处理模块 - 下载和转换微信图片
"""

import requests
import base64
import os
import time
from typing import Optional, Tuple


class ImageHandler:
    def __init__(self, temp_dir: str = "data/images"):
        """
        初始化图片处理器
        
        Args:
            temp_dir: 临时图片存储目录
        """
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)
        
    def download_wechat_image(self, media_id: str, access_token: str) -> Optional[str]:
        """
        从微信服务器下载图片
        
        Args:
            media_id: 微信图片的media_id
            access_token: 微信access_token
            
        Returns:
            图片保存的本地路径，失败返回None
        """
        try:
            # 微信图片下载接口
            url = f"https://api.weixin.qq.com/cgi-bin/media/get?access_token={access_token}&media_id={media_id}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # 保存图片
                filename = f"{media_id}_{int(time.time())}.jpg"
                filepath = os.path.join(self.temp_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"✓ 图片下载成功: {filepath}")
                return filepath
            else:
                print(f"下载图片失败: {response.status_code}")
                print(f"错误信息: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"下载图片异常: {e}")
            return None
    
    def image_to_base64(self, image_path: str) -> Optional[str]:
        """
        将图片转换为base64编码
        
        Args:
            image_path: 图片路径
            
        Returns:
            base64编码的字符串
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
                base64_str = base64.b64encode(image_data).decode('utf-8')
                return base64_str
        except Exception as e:
            print(f"图片转base64失败: {e}")
            return None
    
    def download_image_from_url(self, image_url: str) -> Optional[str]:
        """
        从URL下载图片（微信图片URL）
        
        Args:
            image_url: 图片URL
            
        Returns:
            图片保存的本地路径
        """
        try:
            response = requests.get(image_url, timeout=10)
            
            if response.status_code == 200:
                # 生成文件名
                filename = f"img_{int(time.time())}.jpg"
                filepath = os.path.join(self.temp_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"✓ 图片下载成功: {filepath}")
                return filepath
            else:
                print(f"下载图片失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"下载图片异常: {e}")
            return None
    
    def get_image_base64_from_url(self, image_url: str) -> Optional[str]:
        """
        直接从URL获取图片的base64编码
        
        Args:
            image_url: 图片URL
            
        Returns:
            base64编码的字符串
        """
        try:
            response = requests.get(image_url, timeout=10)
            
            if response.status_code == 200:
                base64_str = base64.b64encode(response.content).decode('utf-8')
                return base64_str
            else:
                print(f"下载图片失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"获取图片base64异常: {e}")
            return None
    
    def cleanup_old_images(self, max_age_hours: int = 24):
        """
        清理旧图片
        
        Args:
            max_age_hours: 保留时间（小时）
        """
        try:
            now = time.time()
            max_age_seconds = max_age_hours * 3600
            cleaned = 0
            
            for filename in os.listdir(self.temp_dir):
                filepath = os.path.join(self.temp_dir, filename)
                
                # 检查文件年龄
                if os.path.isfile(filepath):
                    file_age = now - os.path.getmtime(filepath)
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        cleaned += 1
            
            if cleaned > 0:
                print(f"清理了 {cleaned} 个旧图片")
            
            return cleaned
            
        except Exception as e:
            print(f"清理图片失败: {e}")
            return 0


# 全局图片处理器实例
image_handler = ImageHandler()
"""
阿里云OSS工具模块

提供OSS上传、删除等操作的封装
"""

import oss2
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.core.logger import app_logger


class OSSClient:
    """OSS客户端类"""
    
    def __init__(self):
        """初始化OSS客户端"""
        self.auth = oss2.Auth(
            settings.OSS_ACCESS_KEY_ID,
            settings.OSS_ACCESS_KEY_SECRET
        )
        self.bucket = oss2.Bucket(
            self.auth,
            settings.OSS_ENDPOINT,
            settings.OSS_BUCKET_NAME
        )
    
    def upload_file(self, file_content: bytes, file_ext: str, key_prefix: str = "uploads/") -> str:
        """
        上传文件到OSS
        
        Args:
            file_content: 文件内容
            file_ext: 文件扩展名，例如".jpg"
            key_prefix: OSS存储路径前缀
            
        Returns:
            str: 文件的访问URL
        """
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        object_key = f"{key_prefix}{year}/{month}/{unique_filename}"
        
        try:
            self.bucket.put_object(object_key, file_content)
            app_logger.info(f"文件上传成功: {object_key}")
            
            if settings.OSS_CDN_DOMAIN:
                return f"https://{settings.OSS_CDN_DOMAIN}/{object_key}"
            else:
                return f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{object_key}"
        except Exception as e:
            app_logger.error(f"文件上传失败: {str(e)}")
            raise
    
    def delete_file(self, object_key: str) -> bool:
        """
        从OSS删除文件
        
        Args:
            object_key: OSS对象键
            
        Returns:
            bool: 删除是否成功
        """
        try:
            self.bucket.delete_object(object_key)
            app_logger.info(f"文件删除成功: {object_key}")
            return True
        except Exception as e:
            app_logger.error(f"文件删除失败: {str(e)}")
            return False

    def get_file_content(self, object_key: str) -> bytes:
        """
        从OSS获取文件内容 (用于后端处理)

        Args:
            object_key: OSS对象键 (例如: voice_samples/xxx.mp3)

        Returns:
            bytes: 文件字节流内容
        """
        try:
            # get_object 返回的是一个 file-like object
            result = self.bucket.get_object(object_key)
            content = result.read()
            app_logger.info(f"文件拉取成功: {object_key}")
            return content
        except Exception as e:
            app_logger.error(f"文件拉取失败: {str(e)}")
            raise

    def get_sign_url(self, object_key: str, expires: int = 3600) -> str:
        """
        生成有时效性的签名访问链接

        Args:
            object_key: OSS对象键
            expires: 有效期（秒），默认1小时

        Returns:
            str: 签名URL
        """
        try:
            # 即使文件是私有的，生成的 URL 也可以直接访问
            url = self.bucket.sign_url('GET', object_key, expires)
            app_logger.info(f"签名URL生成成功: {object_key}")
            return url
        except Exception as e:
            app_logger.error(f"签名URL生成失败: {str(e)}")
            raise

oss_client = OSSClient()

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


oss_client = OSSClient()

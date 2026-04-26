"""
阿里云OSS工具模块

提供OSS上传、删除、拉取和签名URL等操作的封装。
"""

import uuid
from datetime import datetime
from urllib.parse import urlparse

import oss2

from app.core.config import settings
from app.core.logger import app_logger


class OSSClient:
    """OSS客户端类"""

    def __init__(self):
        self.auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
        self.bucket = oss2.Bucket(self.auth, settings.OSS_ENDPOINT, settings.OSS_BUCKET_NAME)

    def upload_file(self, file_content: bytes, file_ext: str, key_prefix: str = "uploads/") -> str:
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        normalized_key_prefix = key_prefix.rstrip("/") + "/"
        object_key = f"{normalized_key_prefix}{year}/{month}/{unique_filename}"

        try:
            self.bucket.put_object(object_key, file_content)
            app_logger.info(f"文件上传成功: {object_key}")
            if settings.OSS_CDN_DOMAIN:
                return f"https://{settings.OSS_CDN_DOMAIN}/{object_key}"
            return f"https://{settings.OSS_BUCKET_NAME}.{settings.OSS_ENDPOINT}/{object_key}"
        except Exception as e:
            app_logger.error(f"文件上传失败: {str(e)}")
            raise

    def delete_file(self, object_key: str) -> bool:
        try:
            self.bucket.delete_object(object_key)
            app_logger.info(f"文件删除成功: {object_key}")
            return True
        except Exception as e:
            app_logger.error(f"文件删除失败: {str(e)}")
            return False

    def get_file_content(self, object_key: str) -> bytes:
        try:
            result = self.bucket.get_object(object_key)
            content = result.read()
            app_logger.info(f"文件拉取成功: {object_key}")
            return content
        except Exception as e:
            app_logger.error(f"文件拉取失败: {str(e)}")
            raise

    def get_object_key_from_url(self, file_url: str) -> str:
        parsed = urlparse(file_url)
        path = parsed.path.lstrip("/")
        if not path:
            raise ValueError(f"无法从URL解析对象键: {file_url}")
        return path

    def get_sign_url(self, object_key: str, expires: int = 3600) -> str:
        try:
            url = self.bucket.sign_url("GET", object_key, expires)
            app_logger.info(f"签名URL生成成功: {object_key}")
            return url
        except Exception as e:
            app_logger.error(f"签名URL生成失败: {str(e)}")
            raise

    def get_sign_url_from_file_url(self, file_url: str, expires: int = 3600) -> str:
        object_key = self.get_object_key_from_url(file_url)
        return self.get_sign_url(object_key, expires)


oss_client = OSSClient()

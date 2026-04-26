import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch
from main import app


# ================= 测试用例 =================

@pytest.mark.asyncio
# 🎯 核心技术：使用 patch 拦截对真实 OSS 的调用
@patch("app.api.common.oss_client.upload_file")
async def test_upload_success(mock_upload):
    """测试: 成功上传合法文件"""
    print("\n" + "=" * 15 + " 测试: 正常文件上传 (Mock OSS) " + "=" * 15)

    # 配置 Mock 对象的返回值，假装 OSS 上传成功并返回了一个 URL
    fake_oss_url = "https://mock-oss-bucket.oss-cn-hangzhou.aliyuncs.com/test_image.png"
    mock_upload.return_value = fake_oss_url

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 构造模拟的文件数据
        fake_file_content = b"fake image byte content"
        files = {"file": ("test_image.png", fake_file_content, "image/png")}

        # 发起无鉴权上传请求 (因为 get_current_user_optional 允许匿名)
        response = await ac.post("/common/upload", files=files)

        print(f"[正常上传] 响应数据: {response.json()}")

        assert response.status_code == 200
        # ⚠️ 注意：这里断言的是 msg 和 code=1，因为 UploadResponse 的定义与其他接口不同
        assert response.json()["code"] == 1
        assert response.json()["msg"] == "上传成功"
        assert response.json()["data"] == fake_oss_url

        # 验证底层代码确实调用了我们的 mock 方法
        mock_upload.assert_called_once()


@pytest.mark.asyncio
async def test_upload_invalid_extension():
    """测试边界: 上传不支持的文件格式"""
    print("\n" + "=" * 15 + " 测试: 拦截非法文件格式 " + "=" * 15)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 构造一个 .txt 文件
        files = {"file": ("danger.txt", b"hack text", "text/plain")}

        response = await ac.post("/common/upload", files=files)

        print(f"[格式拦截] 响应数据: {response.json()}")

        assert response.status_code == 200
        # 抛出 APIException 时，我们自定义异常处理器返回了 HTTP 200 + 内部错误码
        assert response.json()["code"] == 400
        assert "不支持的文件类型" in response.json()["message"]


@pytest.mark.asyncio
async def test_upload_file_too_large():
    """测试边界: 上传超大文件 (超过10MB)"""
    print("\n" + "=" * 15 + " 测试: 拦截超大文件 " + "=" * 15)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 构造一个刚刚超过 10MB 的假文件内容 (10MB + 1字节)
        large_content = b"0" * (10 * 1024 * 1024 + 1)
        files = {"file": ("big_image.png", large_content, "image/png")}

        response = await ac.post("/common/upload", files=files)

        print(f"[大小拦截] 响应数据: {response.json()}")

        assert response.status_code == 200
        assert response.json()["code"] == 400
        assert "文件大小超过限制" in response.json()["message"]

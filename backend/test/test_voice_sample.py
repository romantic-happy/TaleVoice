# backend/tests/test_voice_sample.py

import pytest
from httpx import AsyncClient, ASGITransport
from main import app  # 确保导入你的 FastAPI 实例
from app.core.database import get_db, Base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import pytest_asyncio

# ================= 1. 测试环境配置 (复用之前的内存数据库方案) =================
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ================= 2. 辅助函数：获取登录 Token =================
async def get_auth_headers(ac: AsyncClient, username="audio_tester", password="pwd", email="audio@test.com"):
    """辅助函数：注册并登录，返回携带 Token 的请求头"""
    await ac.post("/api/user/register", json={"username": username, "password": password, "email": email})
    login_res = await ac.post("/api/user/login", json={"username": username, "password": password})
    data = login_res.json().get("data")
    token = data if isinstance(data, str) else data.get("token")
    return {"Authorization": f"Bearer {token}"}


# ================= 3. 开始编写测试用例 =================

@pytest.mark.asyncio
async def test_crud_voice_sample_flow():
    """
    核心业务流测试：完整的增、查、改、删生命周期
    """
    print("\n" + "=" * 15 + " 测试: 音色样本完整生命周期 (CRUD) " + "=" * 15)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await get_auth_headers(ac)

        # ---------------- 步骤 A: 创建音色 (Create) ----------------
        print("\n--- A. 测试创建音色样本 ---")
        create_payload = {"voiceName": "孙悟空音色"}
        create_res = await ac.post("/api/user/audio", json=create_payload, headers=headers)
        create_data = create_res.json()
        print(f"[创建] 请求体: {create_payload}")
        print(f"[创建] 响应数据: {create_data}")
        assert create_res.status_code == 200
        assert create_data["message"] == "创建成功"

        # 提取新创建的 voice_id 供后续使用
        voice_id = create_data["data"]
        assert voice_id is not None

        # ---------------- 步骤 B: 查询列表 (Read) ----------------
        print("\n--- B. 测试获取音色列表 ---")
        list_res = await ac.get("/api/user/audio", headers=headers)
        list_data = list_res.json()
        print(f"[查询] 响应数据: {list_data}")
        assert list_res.status_code == 200
        assert len(list_data["data"]) >= 1
        # 验证刚才创建的音色在列表中
        assert any(item["voiceId"] == voice_id for item in list_data["data"])

        # ---------------- 步骤 C: 修改音色 (Update) ----------------
        print("\n--- C. 测试修改音色名称 ---")
        update_payload = {"voiceId": voice_id, "voiceName": "齐天大圣音色-增强版"}
        update_res = await ac.put("/api/user/audio", json=update_payload, headers=headers)
        print(f"[修改] 请求体: {update_payload}")
        print(f"[修改] 响应数据: {update_res.json()}")
        assert update_res.status_code == 200
        assert update_res.json()["message"] == "修改成功"

        # ---------------- 步骤 D: 删除音色 (Delete) ----------------
        print("\n--- D. 测试删除音色样本 ---")
        delete_res = await ac.delete(f"/api/user/audio/{voice_id}", headers=headers)
        print(f"[删除] 请求 URL: /api/user/audio/{voice_id}")
        print(f"[删除] 响应数据: {delete_res.json()}")
        assert delete_res.status_code == 200
        assert delete_res.json()["message"] == "删除成功"

        # ---------------- 步骤 E: 验证删除结果 ----------------
        verify_res = await ac.get("/api/user/audio", headers=headers)
        print(f"[验证] 再次获取列表，确认是否删除: {verify_res.json()}")
        assert not any(item["voiceId"] == voice_id for item in verify_res.json()["data"])


@pytest.mark.asyncio
async def test_error_boundary_cases():
    """
    边界测试：操作不存在的记录
    """
    print("\n" + "=" * 15 + " 测试: 异常边界情况处理 (404 Not Found) " + "=" * 15)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await get_auth_headers(ac, username="boundary_user", email="b@test.com")
        fake_id = "this-is-a-fake-uuid-1234"

        # 1. 尝试修改不存在的音色
        update_payload = {"voiceId": fake_id, "voiceName": "幽灵音色"}
        update_res = await ac.put("/api/user/audio", json=update_payload, headers=headers)
        print(f"[异常修改] 请求体: {update_payload}")
        print(f"[异常修改] 响应数据: {update_res.json()}")
        # 因为我们有统一的异常处理转换成了 HTTP 200 + 内部错误码，这里检查业务逻辑是否拦截
        assert "不存在" in update_res.json()["message"]

        # 2. 尝试删除不存在的音色
        delete_res = await ac.delete(f"/api/user/audio/{fake_id}", headers=headers)
        print(f"[异常删除] 请求 URL: /api/user/audio/{fake_id}")
        print(f"[异常删除] 响应数据: {delete_res.json()}")
        assert "不存在" in delete_res.json()["message"]

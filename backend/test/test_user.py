# backend/tests/test_user.py

import pytest
from httpx import AsyncClient, ASGITransport
from main import app  # 确保这能正确导入你的 FastAPI 实例
from app.core.database import get_db, Base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import pytest_asyncio

# 1. 覆盖数据库依赖 (使用内存 SQLite，不污染真实数据库)
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
TestingSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


# 2. 数据库初始化与清理的 Fixture
@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# --- 辅助函数：快速注册登录并获取 Token Header ---
async def get_auth_headers(ac: AsyncClient, username="testuser", password="password123", email="test@example.com"):
    # 先注册
    await ac.post("/api/user/register", json={
        "username": username, "password": password, "email": email
    })
    # 后登录
    login_res = await ac.post("/api/user/login", json={
        "username": username, "password": password
    })

    # 智能提取 Token (兼容 data 是字符串或字典的情况)
    data = login_res.json().get("data")
    token = data if isinstance(data, str) else (data.get("token") or data.get("access_token"))
    return {"Authorization": f"Bearer {token}"}


# ================= 开始编写测试用例 =================

@pytest.mark.asyncio
async def test_register_and_login():
    print("\n" + "=" * 15 + " 测试: 注册与登录 " + "=" * 15)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. 测试注册
        reg_payload = {"username": "user1", "password": "pwd123", "email": "u1@test.com"}
        reg_res = await ac.post("/api/user/register", json=reg_payload)
        print(f"[注册] 请求体: {reg_payload}")
        print(f"[注册] 响应状态码: {reg_res.status_code}")
        print(f"[注册] 响应数据: {reg_res.json()}")
        assert reg_res.status_code == 200

        # 2. 测试登录
        login_payload = {"username": "user1", "password": "pwd123"}
        login_res = await ac.post("/api/user/login", json=login_payload)
        print(f"[登录] 请求体: {login_payload}")
        print(f"[登录] 响应数据: {login_res.json()}")
        assert login_res.status_code == 200


@pytest.mark.asyncio
async def test_get_and_update_profile():
    print("\n" + "=" * 15 + " 测试: 获取与修改个人资料 " + "=" * 15)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await get_auth_headers(ac)

        # 1. 获取资料
        get_res = await ac.get("/api/user/profile", headers=headers)
        print(f"[获取资料] 响应数据: {get_res.json()}")
        assert get_res.status_code == 200

        # 2. 修改资料
        update_payload = {"username": "new_name", "email": "new@test.com", "avatar": "http://img.com/1.jpg"}
        put_res = await ac.put("/api/user/profile", json=update_payload, headers=headers)
        print(f"[修改资料] 请求体: {update_payload}")
        print(f"[修改资料] 响应数据: {put_res.json()}")
        assert put_res.status_code == 200

        # 3. 再次获取验证是否修改成功
        verify_res = await ac.get("/api/user/profile", headers=headers)
        print(f"[验证修改后资料] 响应数据: {verify_res.json()}")
        assert verify_res.json()["data"]["username"] == "new_name"


@pytest.mark.asyncio
async def test_change_password():
    print("\n" + "=" * 15 + " 测试: 修改密码 " + "=" * 15)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await get_auth_headers(ac, username="pwduser", password="old123", email="p@test.com")

        # 1. 修改密码
        pwd_payload = {"oldPassword": "old123", "newPassword": "new123"}
        pwd_res = await ac.put("/api/user/password", json=pwd_payload, headers=headers)
        print(f"[修改密码] 请求体: {pwd_payload}")
        print(f"[修改密码] 响应数据: {pwd_res.json()}")
        assert pwd_res.status_code == 200

        # 2. 用新密码尝试登录
        login_res = await ac.post("/api/user/login", json={"username": "pwduser", "password": "new123"})
        print(f"[新密码登录] 响应数据: {login_res.json()}")
        assert login_res.status_code == 200


@pytest.mark.asyncio
async def test_logout():
    print("\n" + "=" * 15 + " 测试: 退出登录 " + "=" * 15)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await get_auth_headers(ac)

        logout_res = await ac.post("/api/user/logout", headers=headers)
        print(f"[退出登录] 响应数据: {logout_res.json()}")
        assert logout_res.status_code == 200


@pytest.mark.asyncio
async def test_reset_password():
    print("\n" + "=" * 15 + " 测试: 密码重置邮件发送 " + "=" * 15)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 该接口无需鉴权
        reset_payload = {"email": "test@example.com"}
        reset_res = await ac.post("/api/user/password/reset", json=reset_payload)
        print(f"[重置密码] 请求体: {reset_payload}")
        print(f"[重置密码] 响应数据: {reset_res.json()}")
        assert reset_res.status_code == 200

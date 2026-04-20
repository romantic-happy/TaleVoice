import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.core.database import get_db, Base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import pytest_asyncio

# ================= 1. 测试环境配置 (内存数据库) =================
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
async def get_auth_headers(ac: AsyncClient, username="proj_tester", password="pwd", email="proj@test.com"):
    await ac.post("/api/user/register", json={"username": username, "password": password, "email": email})
    login_res = await ac.post("/api/user/login", json={"username": username, "password": password})
    data = login_res.json().get("data")
    token = data if isinstance(data, str) else data.get("token")
    return {"Authorization": f"Bearer {token}"}


# ================= 3. 开始编写测试用例 =================

@pytest.mark.asyncio
async def test_crud_project_flow():
    """测试项目核心流：创建、修改、删除"""
    print("\n" + "=" * 15 + " 测试: 项目完整生命周期 (CRUD) " + "=" * 15)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await get_auth_headers(ac)

        # 1. 创建项目
        create_payload = {"title": "我的第一个绘本", "description": "讲述森林里的故事", "style": "童话水彩"}
        create_res = await ac.post("/api/project", json=create_payload, headers=headers)
        print(f"[创建项目] 响应: {create_res.json()}")
        assert create_res.status_code == 200
        project_id = create_res.json()["data"]
        assert project_id is not None

        # 2. 修改项目
        update_payload = {
            "projectId": project_id,
            "title": "修改后的绘本标题",
            "description": "内容更新了",
            "style": "赛博朋克"
        }
        update_res = await ac.put("/api/project", json=update_payload, headers=headers)
        print(f"[修改项目] 响应: {update_res.json()}")
        assert update_res.status_code == 200

        # 3. 删除项目
        delete_res = await ac.delete(f"/api/project/{project_id}", headers=headers)
        print(f"[删除项目] 响应: {delete_res.json()}")
        assert delete_res.status_code == 200


@pytest.mark.asyncio
async def test_project_pagination_and_search():
    """高级测试：测试列表的分页与关键字搜索功能"""
    print("\n" + "=" * 15 + " 测试: 列表分页与搜索功能 " + "=" * 15)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = await get_auth_headers(ac, username="search_user", email="s@test.com")

        # 1. 批量创建 3 个项目用于测试搜索
        projects_to_create = [
            {"title": "魔法学院的秘密", "description": "d1", "style": "s1"},
            {"title": "太空冒险指南", "description": "d2", "style": "s2"},
            {"title": "海底学院奇遇记", "description": "d3", "style": "s3"}
        ]
        for p in projects_to_create:
            await ac.post("/api/project", json=p, headers=headers)
        print("[初始化] 已成功创建 3 个测试项目。")

        # 2. 测试分页：查第1页，每页2条
        page_res = await ac.get("/api/project/list?page=1&pageSize=2", headers=headers)
        page_data = page_res.json()
        print(f"[分页测试] 请求 page=1, pageSize=2 的响应: {page_data}")

        payload = page_data.get("data")

        assert payload["total"] == 3  # 数据库总共3条
        assert len(payload["lists"]) == 2  # 但当前页只返回2条

        # 3. 测试搜索：搜索标题包含“学院”的项目 (应该返回 2 条记录)
        search_res = await ac.get("/api/project/list?title=学院", headers=headers)
        search_data = search_res.json()
        print(f"[搜索测试] 搜索关键字'学院'的响应: {search_data}")

        payload_search = search_data.get("data") or search_data.get("date")
        assert payload_search["total"] == 2
        # 验证返回的标题里确实包含"学院"
        assert all("学院" in item["title"] for item in payload_search["lists"])

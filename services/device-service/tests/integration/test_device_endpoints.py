import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.session import get_db
from app.models.device import Base


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        yield session
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestDeviceEndpoints:
    """Integration tests for device endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """GET /health should return 200."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_create_device(self, client):
        """POST /api/v1/devices should return 201."""
        response = await client.post(
            "/api/v1/devices",
            json={
                "device_id": "COMPRESSOR-001",
                "device_name": "Test Compressor",
                "device_type": "compressor"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["device_id"] == "COMPRESSOR-001"
    
    @pytest.mark.asyncio
    async def test_duplicate_device_returns_409(self, client):
        """POST duplicate device should return 409."""
        await client.post(
            "/api/v1/devices",
            json={
                "device_id": "COMPRESSOR-001",
                "device_name": "Test",
                "device_type": "compressor"
            }
        )
        
        response = await client.post(
            "/api/v1/devices",
            json={
                "device_id": "COMPRESSOR-001",
                "device_name": "Test 2",
                "device_type": "compressor"
            }
        )
        
        assert response.status_code == 409
    
    @pytest.mark.asyncio
    async def test_get_device(self, client):
        """GET /api/v1/devices/{id} should return device."""
        await client.post(
            "/api/v1/devices",
            json={
                "device_id": "COMPRESSOR-001",
                "device_name": "Test",
                "device_type": "compressor"
            }
        )
        
        response = await client.get("/api/v1/devices/COMPRESSOR-001")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["device_id"] == "COMPRESSOR-001"
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_device_returns_404(self, client):
        """GET nonexistent device should return 404."""
        response = await client.get("/api/v1/devices/NONEXISTENT")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_devices_list(self, client):
        """GET /api/v1/devices should return paginated list."""
        response = await client.get("/api/v1/devices")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "pagination" in data
    
    @pytest.mark.asyncio
    async def test_update_device(self, client):
        """PUT /api/v1/devices/{id} should update device."""
        await client.post(
            "/api/v1/devices",
            json={
                "device_id": "COMPRESSOR-001",
                "device_name": "Test",
                "device_type": "compressor"
            }
        )
        
        response = await client.put(
            "/api/v1/devices/COMPRESSOR-001",
            json={"device_name": "Updated Name"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["device_name"] == "Updated Name"
    
    @pytest.mark.asyncio
    async def test_delete_device(self, client):
        """DELETE /api/v1/devices/{id} should soft delete."""
        await client.post(
            "/api/v1/devices",
            json={
                "device_id": "COMPRESSOR-001",
                "device_name": "Test",
                "device_type": "compressor"
            }
        )
        
        response = await client.delete("/api/v1/devices/COMPRESSOR-001")
        assert response.status_code == 200
        
        get_response = await client.get("/api/v1/devices/COMPRESSOR-001")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_heartbeat(self, client):
        """POST /api/v1/devices/{id}/heartbeat should update timestamp."""
        await client.post(
            "/api/v1/devices",
            json={
                "device_id": "COMPRESSOR-001",
                "device_name": "Test",
                "device_type": "compressor"
            }
        )
        
        response = await client.post("/api/v1/devices/COMPRESSOR-001/heartbeat")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["last_seen_timestamp"] is not None
    
    @pytest.mark.asyncio
    async def test_response_envelope_success(self, client):
        """All 200/201 responses should have success=true."""
        response = await client.get("/health")
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_response_envelope_error(self, client):
        """Error responses should have success=false."""
        response = await client.get("/api/v1/devices/NONEXISTENT")
        data = response.json()
        assert data["success"] is False

import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_db_session():
    """Mock database session for unit tests."""
    session = AsyncMock()
    return session


@pytest.fixture
def sample_device_data():
    """Sample device data for testing."""
    return {
        "device_id": "COMPRESSOR-001",
        "device_name": "Test Compressor",
        "device_type": "compressor",
        "location": "Building A",
        "phase_type": "three",
        "manufacturer": "TestCo",
        "model": "TC-1000"
    }


@pytest.fixture
def sample_telemetry():
    """Sample telemetry data for health score tests."""
    return {
        "temperature": 25.0,
        "pressure": 5.0,
        "vibration": 2.5,
        "power": 150.0
    }


@pytest.fixture
def sample_health_configs():
    """Sample health config for testing."""
    return [
        {
            "parameter_name": "temperature",
            "normal_min": 20.0,
            "normal_max": 30.0,
            "max_min": 10.0,
            "max_max": 40.0,
            "weight": 30.0
        },
        {
            "parameter_name": "pressure",
            "normal_min": 4.0,
            "normal_max": 6.0,
            "max_min": 2.0,
            "max_max": 8.0,
            "weight": 30.0
        },
        {
            "parameter_name": "vibration",
            "normal_min": 0.0,
            "normal_max": 5.0,
            "max_min": 0.0,
            "max_max": 10.0,
            "weight": 40.0
        }
    ]

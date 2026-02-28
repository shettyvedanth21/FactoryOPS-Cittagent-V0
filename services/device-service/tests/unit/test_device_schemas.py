import pytest
from pydantic import ValidationError
from app.models.schemas import DeviceCreate, DeviceUpdate, HealthConfigCreate


class TestDeviceSchemas:
    """Test Pydantic schemas for device validation."""
    
    def test_valid_device_id_passes_regex(self):
        """Valid device_id should pass regex validation."""
        device = DeviceCreate(
            device_id="COMPRESSOR-001",
            device_name="Test Compressor",
            device_type="compressor"
        )
        
        assert device.device_id == "COMPRESSOR-001"
    
    def test_invalid_device_id_lowercase_fails(self):
        """Invalid device_id (lowercase) should fail validation."""
        with pytest.raises(ValidationError):
            DeviceCreate(
                device_id="compressor-001",
                device_name="Test",
                device_type="compressor"
            )
    
    def test_weight_over_100_fails_validation(self):
        """Weight > 100 should fail validation."""
        with pytest.raises(ValidationError):
            HealthConfigCreate(
                parameter_name="temperature",
                weight=101.0
            )
    
    def test_weight_negative_fails_validation(self):
        """Negative weight should fail validation."""
        with pytest.raises(ValidationError):
            HealthConfigCreate(
                parameter_name="temperature",
                weight=-1.0
            )
    
    def test_invalid_device_type_fails_validation(self):
        """Invalid device_type should fail validation."""
        with pytest.raises(ValidationError):
            DeviceCreate(
                device_id="TEST-001",
                device_name="Test",
                device_type="invalid_type"
            )
    
    def test_valid_device_type_passes(self):
        """Valid device_type should pass."""
        device = DeviceCreate(
            device_id="TEST-001",
            device_name="Test",
            device_type="compressor"
        )
        
        assert device.device_type == "compressor"
    
    def test_optional_fields_can_be_none(self):
        """Optional fields should accept None."""
        device = DeviceCreate(
            device_id="TEST-001",
            device_name="Test",
            device_type="compressor",
            manufacturer=None,
            model=None,
            location=None
        )
        
        assert device.manufacturer is None
    
    def test_phase_type_validation(self):
        """phase_type should only accept 'single' or 'three'."""
        device = DeviceCreate(
            device_id="TEST-001",
            device_name="Test",
            device_type="motor",
            phase_type="single"
        )
        
        assert device.phase_type == "single"
        
        device2 = DeviceCreate(
            device_id="TEST-002",
            device_name="Test",
            device_type="motor",
            phase_type="three"
        )
        
        assert device2.phase_type == "three"
    
    def test_phase_type_invalid_fails(self):
        """Invalid phase_type should fail."""
        with pytest.raises(ValidationError):
            DeviceCreate(
                device_id="TEST-001",
                device_name="Test",
                device_type="motor",
                phase_type="dual"
            )

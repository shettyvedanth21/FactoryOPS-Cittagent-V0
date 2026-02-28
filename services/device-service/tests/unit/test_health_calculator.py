import pytest
from datetime import time
from app.services.health_calculator import calculate_health_score, get_health_grade
from app.models.device import ParameterHealthConfig


class MockHealthConfig:
    def __init__(
        self,
        parameter_name: str,
        normal_min: float,
        normal_max: float,
        max_min: float,
        max_max: float,
        weight: float,
        ignore_zero_value: bool = False,
        is_active: bool = True
    ):
        self.parameter_name = parameter_name
        self.normal_min = normal_min
        self.normal_max = normal_max
        self.max_min = max_min
        self.max_max = max_max
        self.weight = weight
        self.ignore_zero_value = ignore_zero_value
        self.is_active = is_active


class TestHealthCalculator:
    """Test health score calculation per LLD §4."""
    
    def test_all_values_in_normal_range_score_100(self):
        """All values in normal range should yield score = 100."""
        configs = [
            MockHealthConfig("temperature", 20, 30, 10, 40, 50),
            MockHealthConfig("pressure", 4, 6, 2, 8, 50),
        ]
        telemetry = {"temperature": 25, "pressure": 5}
        
        result = calculate_health_score(configs, telemetry)
        
        assert result["health_score"] == 100.0
        assert result["grade"] == "Excellent"
    
    def test_all_values_at_max_boundary_score_0(self):
        """Values at max boundary should yield score = 0."""
        configs = [
            MockHealthConfig("temp", 20, 30, 10, 40, 100),
        ]
        telemetry = {"temp": 10}
        
        result = calculate_health_score(configs, telemetry)
        
        assert result["health_score"] == 0.0
        assert result["grade"] == "Poor"
    
    def test_parameter_at_normal_min_score_100(self):
        """Parameter at normal_min boundary should score 100."""
        configs = [
            MockHealthConfig("temp", 20, 30, 10, 40, 100),
        ]
        telemetry = {"temp": 20}
        
        result = calculate_health_score(configs, telemetry)
        
        assert result["health_score"] == 100.0
    
    def test_parameter_between_normal_and_max_linear_interpolation(self):
        """Parameter between normal_max and max_max should have linear interpolation."""
        configs = [
            MockHealthConfig("temp", 20, 30, 10, 40, 100),
        ]
        telemetry = {"temp": 35}
        
        result = calculate_health_score(configs, telemetry)
        
        assert 0 < result["health_score"] < 100
    
    def test_ignore_zero_value_and_value_0_skipped(self):
        """Parameter with ignore_zero_value=True and value=0 should be skipped."""
        configs = [
            MockHealthConfig("power", 0, 100, -10, 110, 100, ignore_zero_value=True),
        ]
        telemetry = {"power": 0}
        
        result = calculate_health_score(configs, telemetry)
        
        assert result["skipped_parameters"] == 1
        assert result["evaluated_parameters"] == 0
    
    def test_missing_parameter_in_telemetry_skipped(self):
        """Missing parameter in telemetry should be skipped."""
        configs = [
            MockHealthConfig("temp", 20, 30, 10, 40, 50),
            MockHealthConfig("pressure", 4, 6, 2, 8, 50),
        ]
        telemetry = {"temp": 25}
        
        result = calculate_health_score(configs, telemetry)
        
        assert result["skipped_parameters"] == 1
        assert result["evaluated_parameters"] == 1
    
    def test_partial_weights_normalized_correctly(self):
        """Partial weights that don't sum to 100 should be normalized."""
        configs = [
            MockHealthConfig("temp", 20, 30, 10, 40, 30),
            MockHealthConfig("pressure", 4, 6, 2, 8, 20),
        ]
        telemetry = {"temp": 25, "pressure": 5}
        
        result = calculate_health_score(configs, telemetry)
        
        assert result["health_score"] == 100.0
    
    def test_grade_excellent(self):
        """Score 95 should yield 'Excellent' grade."""
        assert get_health_grade(95) == "Excellent"
        assert get_health_grade(100) == "Excellent"
    
    def test_grade_good(self):
        """Score 75 should yield 'Good' grade."""
        assert get_health_grade(75) == "Good"
        assert get_health_grade(89) == "Good"
    
    def test_grade_fair(self):
        """Score 60 should yield 'Fair' grade."""
        assert get_health_grade(60) == "Fair"
        assert get_health_grade(69) == "Fair"
    
    def test_grade_poor(self):
        """Score 40 should yield 'Poor' grade."""
        assert get_health_grade(40) == "Poor"
        assert get_health_grade(0) == "Poor"
    
    def test_empty_telemetry_score_0(self):
        """Empty telemetry should yield score = 0."""
        configs = [
            MockHealthConfig("temp", 20, 30, 10, 40, 100),
        ]
        telemetry = {}
        
        result = calculate_health_score(configs, telemetry)
        
        assert result["health_score"] == 0.0
        assert result["grade"] == "Poor"

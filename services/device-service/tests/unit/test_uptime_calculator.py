import pytest
from datetime import date
from app.services.uptime_calculator import calculate_scheduled_minutes


class MockShift:
    def __init__(
        self,
        shift_name: str,
        shift_start_hour: int,
        shift_start_minute: int,
        shift_end_hour: int,
        shift_end_minute: int,
        maintenance_break_minutes: int = 0,
        day_of_week: int = None
    ):
        from datetime import time
        self.shift_name = shift_name
        self.shift_start = time(shift_start_hour, shift_start_minute)
        self.shift_end = time(shift_end_hour, shift_end_minute)
        self.maintenance_break_minutes = maintenance_break_minutes
        self.day_of_week = day_of_week


class TestUptimeCalculator:
    """Test uptime calculation per LLD §4."""
    
    def test_no_shifts_returns_zero(self):
        """No shifts configured should return 0 minutes."""
        shifts = []
        start = date(2026, 2, 1)
        end = date(2026, 2, 7)
        
        total, evaluated = calculate_scheduled_minutes(shifts, start, end)
        
        assert total == 0
        assert len(evaluated) == 0
    
    def test_single_shift_monday_to_friday(self):
        """Single shift 9-17 with 30min break for 5 days = correct minutes."""
        shifts = [
            MockShift(
                "Morning Shift",
                9, 0,
                17, 0,
                maintenance_break_minutes=30,
                day_of_week=None
            )
        ]
        start = date(2026, 2, 2)
        end = date(2026, 2, 6)
        
        total, evaluated = calculate_scheduled_minutes(shifts, start, end)
        
        assert total == 2100
    
    def test_day_specific_shift_only_applies_to_that_day(self):
        """Day-specific shift should only apply to that day."""
        shifts = [
            MockShift(
                "Monday Only",
                9, 0,
                17, 0,
                day_of_week=0
            )
        ]
        start = date(2026, 2, 2)
        end = date(2026, 2, 8)
        
        total, evaluated = calculate_scheduled_minutes(shifts, start, end)
        
        assert total == 480
        assert len(evaluated) == 1
    
    def test_universal_shift_applies_every_day(self):
        """Universal shift (day_of_week=None) should apply every day."""
        shifts = [
            MockShift(
                "All Days",
                8, 0,
                16, 0,
                day_of_week=None
            )
        ]
        start = date(2026, 2, 2)
        end = date(2026, 2, 8)
        
        total, evaluated = calculate_scheduled_minutes(shifts, start, end)
        
        assert total == 480 * 7
        assert len(evaluated) == 7
    
    def test_two_shifts_per_day(self):
        """Two shifts per day should sum correctly."""
        shifts = [
            MockShift("Morning", 6, 0, 14, 0, day_of_week=None),
            MockShift("Evening", 14, 0, 22, 0, day_of_week=None),
        ]
        start = date(2026, 2, 2)
        end = date(2026, 2, 2)
        
        total, evaluated = calculate_scheduled_minutes(shifts, start, end)
        
        assert total == 960

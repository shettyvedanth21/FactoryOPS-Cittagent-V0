import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.rule_evaluator import RuleEvaluator


class TestRuleEvaluator:
    @pytest.fixture
    def evaluator(self):
        return RuleEvaluator()
    
    @pytest.mark.asyncio
    async def test_condition_gt_triggers(self, evaluator):
        result = await evaluator.evaluate_condition(">", 71, 70)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_condition_gt_not_triggers_at_threshold(self, evaluator):
        result = await evaluator.evaluate_condition(">", 70, 70)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_condition_gte_triggers_at_threshold(self, evaluator):
        result = await evaluator.evaluate_condition(">=", 70, 70)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_condition_lt_triggers(self, evaluator):
        result = await evaluator.evaluate_condition("<", 69, 70)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_condition_eq_triggers_within_tolerance(self, evaluator):
        result = await evaluator.evaluate_condition("=", 70.0001, 70)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_condition_eq_does_not_trigger_beyond_tolerance(self, evaluator):
        result = await evaluator.evaluate_condition("=", 70.01, 70)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_condition_neq_triggers(self, evaluator):
        result = await evaluator.evaluate_condition("!=", 71, 70)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_condition_neq_does_not_trigger_within_tolerance(self, evaluator):
        result = await evaluator.evaluate_condition("!=", 70.0001, 70)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_condition_lte_triggers_at_threshold(self, evaluator):
        result = await evaluator.evaluate_condition("<=", 70, 70)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_evaluate_skips_property_not_in_telemetry(self, evaluator):
        mock_db = AsyncMock()
        
        mock_rule = MagicMock()
        mock_rule.rule_id = "rule-1"
        mock_rule.scope = "all_devices"
        mock_rule.property = "temperature"
        mock_rule.condition = ">"
        mock_rule.threshold = 70
        mock_rule.severity = "critical"
        mock_rule.cooldown_minutes = 15
        mock_rule.notification_channels = {}
        mock_rule.device_ids = []
        mock_rule.last_triggered_at = None
        
        with patch.object(evaluator, 'get_active_rules', return_value=[mock_rule]):
            result = await evaluator.evaluate(
                db=mock_db,
                device_id="COMPRESSOR-001",
                telemetry={"pressure": 100}
            )
        
        assert len(result["skipped"]) == 1
        assert "temperature" in result["skipped"][0]["reason"]
    
    @pytest.mark.asyncio
    async def test_evaluate_skips_device_not_in_selected_list(self, evaluator):
        mock_db = AsyncMock()
        
        mock_rule = MagicMock()
        mock_rule.rule_id = "rule-1"
        mock_rule.scope = "selected_devices"
        mock_rule.property = "temperature"
        mock_rule.condition = ">"
        mock_rule.threshold = 70
        mock_rule.severity = "critical"
        mock_rule.cooldown_minutes = 15
        mock_rule.notification_channels = {}
        mock_rule.device_ids = ["COMPRESSOR-002", "COMPRESSOR-003"]
        mock_rule.last_triggered_at = None
        
        with patch.object(evaluator, 'get_active_rules', return_value=[mock_rule]):
            result = await evaluator.evaluate(
                db=mock_db,
                device_id="COMPRESSOR-001",
                telemetry={"temperature": 80}
            )
        
        assert len(result["skipped"]) == 1
        assert "device not in selected devices" in result["skipped"][0]["reason"]
    
    @pytest.mark.asyncio
    async def test_evaluate_applies_to_all_devices(self, evaluator):
        mock_db = AsyncMock()
        
        mock_rule = MagicMock()
        mock_rule.rule_id = "rule-1"
        mock_rule.scope = "all_devices"
        mock_rule.property = "temperature"
        mock_rule.condition = ">"
        mock_rule.threshold = 70
        mock_rule.severity = "critical"
        mock_rule.cooldown_minutes = 15
        mock_rule.notification_channels = {}
        mock_rule.device_ids = []
        mock_rule.last_triggered_at = None
        
        with patch.object(evaluator, 'get_active_rules', return_value=[mock_rule]):
            with patch('app.services.rule_evaluator.cooldown_manager.is_cooling_down', return_value=False):
                with patch('app.services.rule_evaluator.alert_manager.create_alert', new_callable=AsyncMock) as mock_create_alert:
                    mock_alert = MagicMock()
                    mock_alert.alert_id = "alert-1"
                    mock_create_alert.return_value = mock_alert
                    
                    result = await evaluator.evaluate(
                        db=mock_db,
                        device_id="COMPRESSOR-001",
                        telemetry={"temperature": 80}
                    )
        
        assert len(result["alerts"]) == 1
    
    @pytest.mark.asyncio
    async def test_cooldown_prevents_duplicate_alert(self, evaluator):
        mock_db = AsyncMock()
        
        mock_rule = MagicMock()
        mock_rule.rule_id = "rule-1"
        mock_rule.scope = "all_devices"
        mock_rule.property = "temperature"
        mock_rule.condition = ">"
        mock_rule.threshold = 70
        mock_rule.severity = "critical"
        mock_rule.cooldown_minutes = 15
        mock_rule.notification_channels = {}
        mock_rule.device_ids = []
        mock_rule.last_triggered_at = None
        
        with patch.object(evaluator, 'get_active_rules', return_value=[mock_rule]):
            with patch('app.services.rule_evaluator.cooldown_manager.is_cooling_down', return_value=True):
                result = await evaluator.evaluate(
                    db=mock_db,
                    device_id="COMPRESSOR-001",
                    telemetry={"temperature": 80}
                )
        
        assert len(result["skipped"]) == 1
        assert "cooldown active" in result["skipped"][0]["reason"]
    
    @pytest.mark.asyncio
    async def test_paused_rule_not_evaluated(self, evaluator):
        mock_db = AsyncMock()
        
        mock_rule = MagicMock()
        mock_rule.rule_id = "rule-1"
        mock_rule.scope = "all_devices"
        mock_rule.property = "temperature"
        mock_rule.condition = ">"
        mock_rule.threshold = 70
        mock_rule.severity = "critical"
        mock_rule.cooldown_minutes = 15
        mock_rule.notification_channels = {}
        mock_rule.device_ids = []
        mock_rule.last_triggered_at = None
        
        mock_rule.status = "paused"
        
        with patch.object(evaluator, 'get_active_rules', return_value=[]):
            result = await evaluator.evaluate(
                db=mock_db,
                device_id="COMPRESSOR-001",
                telemetry={"temperature": 80}
            )
        
        assert result["evaluated"] == 0

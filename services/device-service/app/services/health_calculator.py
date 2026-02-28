from typing import List, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import ParameterHealthConfig, Device


def calculate_health_score(
    health_configs: List[ParameterHealthConfig],
    telemetry: Dict[str, float]
) -> Dict[str, Any]:
    """
    Calculate health score based on telemetry and health configurations.
    
    Algorithm from LLD §4:
    - For each active parameter:
      - If value in [normal_min, normal_max] → score = 100
      - If value in [max_min, normal_min) or (normal_max, max_max] → linear interpolation
      - If value outside [max_min, max_max] → score = 0
      - Skip if ignore_zero_value=True AND value=0
      - Skip if parameter not in telemetry
    - weighted_score = parameter_score * (weight / 100)
    - final_score = sum(weighted_scores) / total_evaluated_weight * 100
    """
    weighted_scores = []
    breakdown = []
    evaluated_parameters = 0
    skipped_parameters = 0
    
    for config in health_configs:
        if not config.is_active:
            continue
        
        param_name = config.parameter_name
        
        if param_name not in telemetry:
            skipped_parameters += 1
            continue
        
        value = telemetry[param_name]
        
        if config.ignore_zero_value and value == 0:
            skipped_parameters += 1
            continue
        
        parameter_score = 0.0
        status = "normal"
        
        normal_min = config.normal_min
        normal_max = config.normal_max
        max_min = config.max_min if config.max_min is not None else normal_min
        max_max = config.max_max if config.max_max is not None else normal_max
        
        if normal_min is None:
            normal_min = float('-inf')
        if normal_max is None:
            normal_max = float('inf')
        if max_min is None:
            max_min = normal_min
        if max_max is None:
            max_max = normal_max
        
        if normal_min <= value <= normal_max:
            parameter_score = 100.0
            status = "normal"
        elif max_min <= value < normal_min:
            if normal_min != max_min:
                parameter_score = 100.0 * (value - max_min) / (normal_min - max_min)
            else:
                parameter_score = 0.0
            status = "warning"
        elif normal_max < value <= max_max:
            if max_max != normal_max:
                parameter_score = 100.0 * (max_max - value) / (max_max - normal_max)
            else:
                parameter_score = 0.0
            status = "warning"
        else:
            parameter_score = 0.0
            status = "critical"
        
        weighted_score = parameter_score * (config.weight / 100.0)
        weighted_scores.append(weighted_score)
        
        breakdown.append({
            "parameter": param_name,
            "score": round(parameter_score, 2),
            "weight": config.weight,
            "value": value,
            "status": status
        })
        evaluated_parameters += 1
    
    if not weighted_scores:
        return {
            "health_score": 0.0,
            "grade": "Poor",
            "breakdown": breakdown,
            "evaluated_parameters": evaluated_parameters,
            "skipped_parameters": skipped_parameters
        }
    
    total_weight = sum(b["weight"] for b in breakdown)
    sum_weighted_scores = sum(weighted_scores)
    
    if total_weight > 0:
        final_score = (sum_weighted_scores / total_weight) * 100
    else:
        final_score = 0.0
    
    final_score = min(100.0, max(0.0, final_score))
    
    grade = get_health_grade(final_score)
    
    return {
        "health_score": round(final_score, 2),
        "grade": grade,
        "breakdown": breakdown,
        "evaluated_parameters": evaluated_parameters,
        "skipped_parameters": skipped_parameters
    }


def get_health_grade(score: float) -> str:
    """Get health grade from score."""
    if score >= 90:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Fair"
    else:
        return "Poor"


async def validate_weights(
    db: AsyncSession,
    device_id: str
) -> Dict[str, Any]:
    """Validate that health config weights sum to 100 (±0.01)."""
    result = await db.execute(
        select(ParameterHealthConfig).where(
            and_(
                ParameterHealthConfig.device_id == device_id,
                ParameterHealthConfig.is_active == True
            )
        )
    )
    configs = result.scalars().all()
    
    total_weight = sum(c.weight for c in configs)
    tolerance = 0.01
    
    if abs(total_weight - 100.0) <= tolerance:
        return {
            "valid": True,
            "total_weight": round(total_weight, 2),
            "message": "Weights are valid"
        }
    else:
        return {
            "valid": False,
            "total_weight": round(total_weight, 2),
            "message": f"Weights must sum to 100.0 (currently {total_weight:.2f})"
        }


async def get_health_configs(
    db: AsyncSession,
    device_id: str
) -> List[ParameterHealthConfig]:
    """Get all health configs for a device."""
    result = await db.execute(
        select(ParameterHealthConfig).where(
            and_(
                ParameterHealthConfig.device_id == device_id,
                ParameterHealthConfig.is_active == True
            )
        )
    )
    return list(result.scalars().all())


async def create_health_config(
    db: AsyncSession,
    device_id: str,
    config_data: dict
) -> ParameterHealthConfig:
    """Create or update a health config (upsert)."""
    from datetime import datetime
    
    result = await db.execute(
        select(ParameterHealthConfig).where(
            and_(
                ParameterHealthConfig.device_id == device_id,
                ParameterHealthConfig.parameter_name == config_data["parameter_name"]
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        for key, value in config_data.items():
            if key != "parameter_name":
                setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        await db.flush()
        return existing
    
    config = ParameterHealthConfig(
        device_id=device_id,
        **config_data,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(config)
    await db.flush()
    return config


async def bulk_create_health_configs(
    db: AsyncSession,
    device_id: str,
    configs: List[dict]
) -> List[ParameterHealthConfig]:
    """Bulk create health configs (replace all active configs)."""
    from datetime import datetime
    
    await db.execute(
        ParameterHealthConfig.__table__.delete().where(
            and_(
                ParameterHealthConfig.device_id == device_id,
                ParameterHealthConfig.is_active == True
            )
        )
    )
    
    now = datetime.utcnow()
    new_configs = []
    
    for config_data in configs:
        config = ParameterHealthConfig(
            device_id=device_id,
            **config_data,
            is_active=True,
            created_at=now,
            updated_at=now
        )
        db.add(config)
        new_configs.append(config)
    
    await db.flush()
    return new_configs

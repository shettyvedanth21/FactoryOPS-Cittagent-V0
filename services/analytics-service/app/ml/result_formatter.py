from typing import Dict, Any, List
import numpy as np
from datetime import datetime


class ResultFormatter:
    """
    Formats ML results into plain language for users.
    All outputs must be user-friendly with context, reasoning, and recommended actions.
    """
    
    @staticmethod
    def format_anomaly_results(
        anomalies: List[Dict[str, Any]],
        df,
        sensitivity: str,
        lookback_days: int
    ) -> Dict[str, Any]:
        """
        Format anomaly detection results into plain language.
        
        Args:
            anomalies: List of anomaly dictionaries from detection
            df: Original DataFrame used for analysis
            sensitivity: Detection sensitivity level
            lookback_days: Number of days analyzed
            
        Returns:
            Formatted results dictionary
        """
        if df.empty or len(anomalies) == 0:
            return {
                "analysis_type": "anomaly_detection",
                "summary": {
                    "total_anomalies": 0,
                    "anomaly_rate_pct": 0.0,
                    "period_analyzed": f"{lookback_days} days",
                    "most_affected_parameter": "None",
                    "health_impact": "Normal"
                },
                "anomalies": [],
                "recommendations": [
                    {"rank": 1, "action": "Continue normal monitoring", "urgency": "Routine"}
                ],
                "data_quality": {
                    "days_analyzed": lookback_days,
                    "data_completeness_pct": 100.0 if not df.empty else 0.0
                }
            }
        
        param_counts = {}
        severity_counts = {"low": 0, "medium": 0, "high": 0}
        
        for anomaly in anomalies:
            for param in anomaly.get("parameters", []):
                param_counts[param] = param_counts.get(param, 0) + 1
            severity = anomaly.get("severity", "medium")
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        most_affected = max(param_counts.items(), key=lambda x: x[1])[0] if param_counts else "None"
        
        total_points = len(df)
        anomaly_rate = (len(anomalies) / total_points * 100) if total_points > 0 else 0
        
        if severity_counts["high"] > 5:
            health_impact = "Critical"
        elif severity_counts["high"] > 0 or severity_counts["medium"] > 3:
            health_impact = "Moderate"
        elif anomaly_rate > 5:
            health_impact = "Low"
        else:
            health_impact = "Normal"
        
        formatted_anomalies = []
        for i, anomaly in enumerate(anomalies[:50]):
            context = anomaly.get("context", "")
            severity = anomaly.get("severity", "medium")
            
            reasoning = ""
            if "exceeded" in context.lower() or "above" in context.lower():
                reasoning = f"Value exceeded normal operating range"
            elif "below" in context.lower():
                reasoning = f"Value dropped below normal operating range"
            elif "spike" in context.lower():
                reasoning = f"Unexpected sudden increase detected"
            else:
                reasoning = f"Anomalous reading detected outside normal patterns"
            
            recommended_action = ResultFormatter._get_anomaly_action(severity, most_affected)
            
            formatted_anomalies.append({
                "timestamp": anomaly.get("timestamp", ""),
                "severity": severity,
                "parameters": anomaly.get("parameters", []),
                "context": context,
                "reasoning": reasoning,
                "recommended_action": recommended_action
            })
        
        recommendations = ResultFormatter._generate_anomaly_recommendations(
            severity_counts, most_affected, health_impact
        )
        
        data_quality = 100.0
        if not df.empty:
            non_null_pct = (df.notna().sum().sum() / (len(df) * len(df.columns))) * 100
            data_quality = round(non_null_pct, 1)
        
        return {
            "analysis_type": "anomaly_detection",
            "summary": {
                "total_anomalies": len(anomalies),
                "anomaly_rate_pct": round(anomaly_rate, 2),
                "period_analyzed": f"{lookback_days} days",
                "most_affected_parameter": most_affected,
                "health_impact": health_impact
            },
            "anomalies": formatted_anomalies,
            "recommendations": recommendations,
            "data_quality": {
                "days_analyzed": lookback_days,
                "data_completeness_pct": data_quality
            }
        }
    
    @staticmethod
    def _get_anomaly_action(severity: str, parameter: str) -> str:
        """Get recommended action based on severity and parameter."""
        actions = {
            ("high", "temperature"): "Inspect cooling system and check for blocked filters immediately",
            ("high", "vibration"): "Stop equipment and inspect bearings for damage",
            ("high", "pressure"): "Check relief valves and pressure regulators",
            ("high", "power_kw"): "Review electrical connections and motor condition",
            ("medium", "temperature"): "Schedule cooling system inspection within 24 hours",
            ("medium", "vibration"): "Monitor closely and plan bearing inspection",
            ("medium", "pressure"): "Check seals and pressure system components",
            ("medium", "power_kw"): "Review power consumption patterns",
            ("low", "temperature"): "Continue monitoring during next shift",
            ("low", "vibration"): "Add to maintenance watchlist",
            ("low", "pressure"): "Note in maintenance log",
            ("low", "power_kw"): "Review for efficiency opportunities"
        }
        
        return actions.get((severity, parameter), f"Investigate {parameter} readings")
    
    @staticmethod
    def _generate_anomaly_recommendations(
        severity_counts: Dict[str, int],
        most_affected: str,
        health_impact: str
    ) -> List[Dict[str, Any]]:
        """Generate ranked recommendations based on severity."""
        recommendations = []
        
        if health_impact == "Critical":
            recommendations.append({
                "rank": 1,
                "action": "Immediately inspect the cooling system and check for obstructions",
                "urgency": "Within 1 hour"
            })
            recommendations.append({
                "rank": 2,
                "action": "Review recent maintenance history for this equipment",
                "urgency": "Within 4 hours"
            })
            recommendations.append({
                "rank": 3,
                "action": "Consider reducing load until inspection complete",
                "urgency": "Within 2 hours"
            })
        elif health_impact == "Moderate":
            recommendations.append({
                "rank": 1,
                "action": f"Schedule {most_affected} system inspection",
                "urgency": "Within 24 hours"
            })
            recommendations.append({
                "rank": 2,
                "action": "Review trend data to identify degradation patterns",
                "urgency": "Within 48 hours"
            })
            recommendations.append({
                "rank": 3,
                "action": "Prepare replacement parts if needed",
                "urgency": "This week"
            })
        elif health_impact == "Low":
            recommendations.append({
                "rank": 1,
                "action": f"Continue monitoring {most_affected} parameter",
                "urgency": "Routine"
            })
            recommendations.append({
                "rank": 2,
                "action": "Include in next scheduled maintenance review",
                "urgency": "Next maintenance window"
            })
        else:
            recommendations.append({
                "rank": 1,
                "action": "Continue normal monitoring operations",
                "urgency": "Routine"
            })
        
        return recommendations
    
    @staticmethod
    def format_failure_prediction_results(
        failure_probability: float,
        risk_factors: List[Dict[str, Any]],
        feature_importances: Dict[str, float],
        days_available: int,
        lookback_days: int
    ) -> Dict[str, Any]:
        """
        Format failure prediction results into plain language.
        
        Args:
            failure_probability: Probability of failure (0-100)
            risk_factors: List of identified risk factors
            feature_importances: Feature importance scores
            days_available: Days of data analyzed
            lookback_days: Number of days requested
            
        Returns:
            Formatted results dictionary
        """
        if failure_probability >= 70:
            failure_risk = "High"
            confidence = "High"
            estimated_life = "Less than 7 days"
        elif failure_probability >= 40:
            failure_risk = "Medium"
            confidence = "Moderate"
            estimated_life = "~15 days"
        elif failure_probability >= 20:
            failure_risk = "Low"
            confidence = "Moderate"
            estimated_life = "~30 days"
        else:
            failure_risk = "Minimal"
            confidence = "Low"
            estimated_life = "60+ days"
        
        formatted_risk_factors = []
        for rf in risk_factors[:5]:
            param = rf.get("parameter", "unknown")
            contribution = rf.get("contribution_pct", 0)
            trend = rf.get("trend", "stable")
            
            context = rf.get("context", "")
            
            reasoning = ""
            if trend == "increasing":
                reasoning = f"Progressive {param} increase is a common precursor to failure"
            elif trend == "decreasing":
                reasoning = f"Declining {param} may indicate degrading performance"
            else:
                reasoning = f"{param} is operating outside optimal range"
            
            formatted_risk_factors.append({
                "parameter": param,
                "contribution_pct": round(contribution, 1),
                "trend": trend,
                "context": context,
                "reasoning": reasoning
            })
        
        recommended_actions = ResultFormatter._generate_failure_recommendations(
            failure_risk, formatted_risk_factors
        )
        
        return {
            "analysis_type": "failure_prediction",
            "summary": {
                "failure_risk": failure_risk,
                "failure_probability_pct": round(failure_probability, 1),
                "estimated_remaining_life": estimated_life,
                "confidence": confidence
            },
            "risk_factors": formatted_risk_factors,
            "recommended_actions": recommended_actions,
            "data_quality": {
                "days_analyzed": days_available,
                "model_confidence": confidence
            }
        }
    
    @staticmethod
    def _generate_failure_recommendations(
        failure_risk: str,
        risk_factors: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate ranked recommendations for failure prevention."""
        recommendations = []
        
        if failure_risk == "High":
            recommendations.append({
                "rank": 1,
                "action": "Schedule immediate inspection of equipment",
                "urgency": "Within 24 hours"
            })
            recommendations.append({
                "rank": 2,
                "action": "Prepare backup equipment or contingency plan",
                "urgency": "Within 48 hours"
            })
            if risk_factors:
                rf = risk_factors[0]
                recommendations.append({
                    "rank": 3,
                    "action": f"Focus inspection on {rf.get('parameter', 'critical components')}",
                    "urgency": "During inspection"
                })
        elif failure_risk == "Medium":
            recommendations.append({
                "rank": 1,
                "action": "Inspect bearings and lubrication system",
                "urgency": "Within 3 days"
            })
            recommendations.append({
                "rank": 2,
                "action": "Review maintenance schedule for potential earlier intervention",
                "urgency": "This week"
            })
            recommendations.append({
                "rank": 3,
                "action": "Increase monitoring frequency",
                "urgency": "Immediately"
            })
        elif failure_risk == "Low":
            recommendations.append({
                "rank": 1,
                "action": "Continue regular monitoring",
                "urgency": "Routine"
            })
            recommendations.append({
                "rank": 2,
                "action": "Plan for inspection during next scheduled maintenance",
                "urgency": "Next maintenance window"
            })
        else:
            recommendations.append({
                "rank": 1,
                "action": "Continue normal operations",
                "urgency": "Routine"
            })
        
        return recommendations


result_formatter = ResultFormatter()

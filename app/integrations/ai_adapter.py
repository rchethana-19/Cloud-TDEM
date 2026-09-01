"""
AI Engine Adapter
Integrates the TDEM Risk Engine for access decision making
"""

from typing import Optional, Dict, Any, List
from app.core.logging import get_logger

logger = get_logger("ai_adapter")

# Import actual AI implementations
try:
    from major_project.service import evaluate_request as ai_evaluate_request
    from major_project.risk_engine import calculate_risk
    from major_project.feature_extractor import extract_features
    from major_project.explain import generate_explanation
    
    AI_AVAILABLE = True
    logger.info("AI Risk Engine successfully imported")
except ImportError as e:
    logger.warning(f"AI Risk Engine import failed: {e}")
    AI_AVAILABLE = False


class AIAdapter:
    """Adapter for integrating the TDEM Risk Engine"""
    
    def __init__(self):
        logger.info("AIAdapter initialized")
    
    async def evaluate_access_request(
        self,
        user_id: str,
        file_id: str,
        request_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Evaluate access request using the AI model.
        
        Request data should contain:
        - login_hour: Hour of day (0-23)
        - trusted_device: 0 or 1
        - country: Country name
        - ip_reputation: Score 0-1
        - vpn_detected: 0 or 1
        - failed_login_attempts: Count
        - browser: Browser name
        - access_frequency: Count
        - file_sensitivity: "Low", "Medium", "High"
        - refresh_frequency: Count
        
        Returns:
            {
                "status": "success",
                "risk_score": float (0-1),
                "decision": "ALLOW" | "REQUIRE_MFA" | "DENY",
                "reasons": [list of explanation strings],
                "model": "Isolation Forest",
                "timestamp": ISO datetime
            }
        """
        if not AI_AVAILABLE:
            logger.warning("AI Engine not available, allowing by default")
            return {
                "status": "degraded",
                "risk_score": 0.0,
                "decision": "ALLOW",
                "reasons": ["AI Engine unavailable"],
                "model": "None",
                "timestamp": None,
            }
        
        try:
            # Call the actual AI service
            result = ai_evaluate_request(request_data)
            logger.debug(f"AI evaluation for {user_id}/{file_id}: {result['decision']} (score: {result['risk_score']})")
            return result
        except Exception as e:
            logger.error(f"AI evaluation failed: {e}")
            return {
                "status": "error",
                "risk_score": 0.5,
                "decision": "REQUIRE_MFA",
                "reasons": ["AI evaluation error"],
                "model": "Isolation Forest",
                "timestamp": None,
                "error": str(e),
            }
    
    async def is_access_allowed(
        self,
        user_id: str,
        file_id: str,
        request_data: Dict[str, Any],
    ) -> bool:
        """
        Quick check if access is allowed.
        
        Returns:
            True if decision is ALLOW, False otherwise
        """
        result = await self.evaluate_access_request(user_id, file_id, request_data)
        return result.get("decision") == "ALLOW"
    
    async def is_mfa_required(
        self,
        user_id: str,
        file_id: str,
        request_data: Dict[str, Any],
    ) -> bool:
        """
        Check if MFA is required.
        
        Returns:
            True if decision is REQUIRE_MFA or DENY, False otherwise
        """
        result = await self.evaluate_access_request(user_id, file_id, request_data)
        return result.get("decision") in ["REQUIRE_MFA", "DENY"]
    
    def format_risk_assessment(
        self,
        evaluation: Dict[str, Any],
    ) -> str:
        """
        Format risk assessment for display.
        
        Args:
            evaluation: Result from evaluate_access_request
        
        Returns:
            Human-readable string
        """
        risk_score = evaluation.get("risk_score", 0.0)
        decision = evaluation.get("decision", "UNKNOWN")
        reasons = evaluation.get("reasons", [])
        
        risk_level = "Low"
        if risk_score >= 0.7:
            risk_level = "High"
        elif risk_score >= 0.3:
            risk_level = "Medium"
        
        message = f"Risk: {risk_level} ({risk_score:.2f}) - {decision}\n"
        if reasons:
            message += "Factors: " + ", ".join(reasons)
        
        return message


# Singleton instance
_ai_adapter = None


def get_ai_adapter() -> AIAdapter:
    """Get AI adapter instance (singleton)"""
    global _ai_adapter
    if _ai_adapter is None:
        _ai_adapter = AIAdapter()
    return _ai_adapter

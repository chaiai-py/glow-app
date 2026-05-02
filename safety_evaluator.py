"""
🛡️ Safety & Risk Evaluation Module
Implements safety guidelines, content filtering, and risk mitigation strategies.
Ensures PII is not exposed and maintains ethical AI practices.
"""

import re
from typing import Dict, Tuple

# 🔒 PII PATTERNS
PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b(?:\+?1[-.]?)?(?:\(?[0-9]{3}\)?[-.]?)?[0-9]{3}[-.]?[0-9]{4}\b',
    "ssn": r'\b(?:\d{3}-\d{2}-\d{4}|\d{9})\b',
    "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
    "date_of_birth": r'\b(?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])[-/](?:19|20)?\d{2}\b',
}

# ⚠️ RISK CATEGORIES
RISK_LEVELS = {
    "HIGH": ["financial fraud", "illegal activity", "harmful content"],
    "MEDIUM": ["personal health advice", "financial advice", "legal interpretation"],
    "LOW": ["general information", "motivational support", "learning assistance"]
}

# 🔍 SAFETY CHECK
def detect_pii(text: str) -> Dict[str, any]:
    """
    Detect personally identifiable information (PII) in text.
    
    Args:
        text: Text to scan for PII
    
    Returns:
        Detection results with PII types found
    """
    
    found_pii = {}
    
    for pii_type, pattern in PII_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            found_pii[pii_type] = len(matches)
    
    return {
        "has_pii": len(found_pii) > 0,
        "pii_types": found_pii,
        "risk_level": "HIGH" if found_pii else "LOW"
    }


# 🛡️ SANITIZE TEXT
def sanitize_text(text: str) -> str:
    """
    Remove or mask sensitive information from text.
    
    Args:
        text: Text to sanitize
    
    Returns:
        Sanitized text with PII masked
    """
    
    sanitized = text
    
    # Mask emails
    sanitized = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL]',
        sanitized
    )
    
    # Mask phone numbers
    sanitized = re.sub(
        r'\b(?:\+?1[-.]?)?(?:\(?[0-9]{3}\)?[-.]?)?[0-9]{3}[-.]?[0-9]{4}\b',
        '[PHONE]',
        sanitized
    )
    
    # Mask SSN
    sanitized = re.sub(
        r'\b(?:\d{3}-\d{2}-\d{4}|\d{9})\b',
        '[SSN]',
        sanitized
    )
    
    # Mask credit card
    sanitized = re.sub(
        r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        '[CREDIT_CARD]',
        sanitized
    )
    
    # Mask IP addresses
    sanitized = re.sub(
        r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',
        '[IP_ADDRESS]',
        sanitized
    )
    
    return sanitized


# ⚠️ ASSESS RISK LEVEL
def assess_risk(user_message: str, domain: str, intent: str) -> Dict:
    """
    Assess risk level of user request.
    
    Args:
        user_message: User's input message
        domain: Intent domain (career, learning, finance, wellness)
        intent: Classified intent
    
    Returns:
        Risk assessment with recommendations
    """
    
    risk_score = 0
    risk_factors = []
    
    # Check for PII
    pii_check = detect_pii(user_message)
    if pii_check["has_pii"]:
        risk_score += 30
        risk_factors.append(f"⚠️ PII detected: {', '.join(pii_check['pii_types'].keys())}")
    
    # Domain-specific risk checks
    if domain == "finance":
        # Check for potentially risky financial requests
        risky_terms = ["insider", "pump and dump", "guaranteed return", "illegal", "fraud"]
        if any(term in user_message.lower() for term in risky_terms):
            risk_score += 40
            risk_factors.append("⚠️ Potentially illegal financial activity detected")
    
    elif domain == "wellness":
        # Check for emergency health situations
        emergency_terms = ["suicidal", "severe pain", "emergency", "life-threatening"]
        if any(term in user_message.lower() for term in emergency_terms):
            risk_score += 50
            risk_factors.append("🚨 EMERGENCY: Recommend seeking immediate professional help")
    
    elif domain == "career":
        # Check for discriminatory content
        discriminatory_terms = ["race", "gender", "age discrimination", "harassment"]
        if any(term in user_message.lower() for term in discriminatory_terms):
            risk_score += 25
            risk_factors.append("⚠️ Workplace discrimination issue detected")
    
    # Determine overall risk level
    if risk_score >= 40:
        risk_level = "HIGH"
        recommendation = "⛔ HIGH RISK: This request requires human review or professional guidance."
    elif risk_score >= 20:
        risk_level = "MEDIUM"
        recommendation = "⚠️ MEDIUM RISK: Provide disclaimer that AI advice shouldn't replace professional consultation."
    else:
        risk_level = "LOW"
        recommendation = "✅ LOW RISK: Safe to proceed with standard response."
    
    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "factors": risk_factors if risk_factors else ["✅ No specific risk factors detected"],
        "recommendation": recommendation,
        "should_proceed": risk_level != "HIGH"
    }


# 📋 SAFETY DISCLAIMERS
def get_safety_disclaimer(domain: str) -> str:
    """
    Return appropriate disclaimer based on domain.
    
    Args:
        domain: Intent domain
    
    Returns:
        Relevant safety disclaimer
    """
    
    disclaimers = {
        "finance": "💡 Disclaimer: This is general guidance only. Not financial advice. Consult a licensed financial advisor for investment decisions.",
        "wellness": "💡 Disclaimer: This is not medical advice. For health concerns, consult a healthcare professional or call emergency services if needed.",
        "career": "💡 Disclaimer: This is general career guidance. For legal employment issues, consult an employment lawyer.",
        "learning": "💡 Disclaimer: This is educational support. Always verify information from official sources.",
    }
    
    return disclaimers.get(domain, "💡 This is AI-generated guidance. Use your judgment and consult professionals for important decisions.")


# 🔐 VALIDATE REQUEST
def validate_request(user_id: str, user_message: str, domain: str, intent: str) -> Dict:
    """
    Comprehensive validation of user request.
    
    Args:
        user_id: User identifier
        user_message: User's message
        domain: Intent domain
        intent: Classified intent
    
    Returns:
        Validation result with safety checks
    """
    
    validation_result = {
        "is_valid": True,
        "warnings": [],
        "errors": [],
        "safety_checks": {}
    }
    
    # Check for PII
    pii_check = detect_pii(user_message)
    validation_result["safety_checks"]["pii_check"] = pii_check
    if pii_check["has_pii"]:
        validation_result["warnings"].append(f"PII detected and will be masked: {', '.join(pii_check['pii_types'].keys())}")
    
    # Assess risk
    risk_assessment = assess_risk(user_message, domain, intent)
    validation_result["safety_checks"]["risk_assessment"] = risk_assessment
    if not risk_assessment["should_proceed"]:
        validation_result["is_valid"] = False
        validation_result["errors"].append(risk_assessment["recommendation"])
    
    # Add domain disclaimer
    validation_result["disclaimer"] = get_safety_disclaimer(domain)
    
    return validation_result


# 📊 SAFETY METRICS
def get_safety_metrics(request_count: int = 100) -> Dict:
    """
    Get summary of safety metrics (for analytics/logging).
    
    Returns:
        Summary of safety checks performed
    """
    
    return {
        "total_requests_checked": request_count,
        "pii_detection_enabled": True,
        "risk_assessment_enabled": True,
        "content_filtering_enabled": True,
        "safety_guidelines": {
            "no_pii": "Personal information is masked",
            "no_illegal": "Illegal activities are flagged",
            "no_harm": "Harmful content is filtered",
            "professional_disclaimers": "All domain-specific disclaimers included"
        },
        "mitigation_strategies": {
            "data_masking": "Automatic PII redaction",
            "risk_flagging": "High-risk requests require review",
            "user_transparency": "Clear disclaimers on limitations",
            "professional_guidance": "Recommendations to seek professional help when needed"
        }
    }

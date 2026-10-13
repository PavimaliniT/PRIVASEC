import re
from typing import Dict, Any, List, Optional


def mask_email(email: str, strategy: str = "PARTIAL") -> str:
    """Masks email address according to chosen strategy."""
    if strategy == "FULL":
        return "****************"
    if strategy == "REDACT":
        return "[REDACTED_EMAIL]"
    
    parts = email.split("@")
    if len(parts) != 2:
        return "********"
    user, domain = parts
    if len(user) <= 1:
        masked_user = "*"
    elif len(user) == 2:
        masked_user = user[0] + "*"
    else:
        masked_user = user[0] + ("*" * (len(user) - 2)) + user[-1]
    return f"{masked_user}@{domain}"


def mask_phone(phone: str, strategy: str = "PARTIAL") -> str:
    """Masks phone number (keeps last 4 digits in partial strategy)."""
    if strategy == "FULL":
        return "**********"
    if strategy == "REDACT":
        return "[REDACTED_PHONE]"
    
    clean = re.sub(r"[^\d]", "", phone)
    if len(clean) <= 4:
        return "****"
    return "*" * (len(clean) - 4) + clean[-4:]


def mask_pan(pan: str, strategy: str = "PARTIAL") -> str:
    """Masks Indian PAN (XXXXX1234X)."""
    if strategy == "FULL":
        return "**********"
    if strategy == "REDACT":
        return "[REDACTED_PAN]"
    
    clean = pan.strip().upper()
    if len(clean) == 10:
        return "XXXXX" + clean[5:9] + clean[9]
    return "XXXXX****X"


def mask_aadhaar(aadhaar: str, strategy: str = "PARTIAL") -> str:
    """Masks Indian Aadhaar (XXXX-XXXX-1234)."""
    if strategy == "FULL":
        return "************"
    if strategy == "REDACT":
        return "[REDACTED_AADHAAR]"
    
    clean = re.sub(r"[^\d]", "", aadhaar)
    if len(clean) == 12:
        return "XXXX-XXXX-" + clean[8:12]
    return "XXXX-XXXX-****"


def mask_credit_card(card: str, strategy: str = "PARTIAL") -> str:
    """Masks Credit Card (************1234)."""
    if strategy == "FULL":
        return "****************"
    if strategy == "REDACT":
        return "[REDACTED_CREDIT_CARD]"
    
    clean = re.sub(r"[^\d]", "", card)
    if len(clean) >= 4:
        return "*" * (len(clean) - 4) + clean[-4:]
    return "************"


def mask_generic(val: str, entity_type: str, strategy: str = "PARTIAL") -> str:
    """Fallback generic masker for names, IP addresses, secrets, etc."""
    if strategy == "FULL":
        return "*" * len(val)
    if strategy == "REDACT":
        return f"[REDACTED_{entity_type}]"
    if len(val) <= 2:
        return "**"
    return val[0] + ("*" * (len(val) - 2)) + val[-1]


def mask_entity_value(val: str, entity_type: str, strategy: str = "PARTIAL", user_role: str = "standard_user") -> str:
    """Dispatches masking based on entity type, strategy, and user role."""
    # Privacy officer and super admin might have elevated view if role-based policy permits
    entity_up = entity_type.upper()
    
    if strategy == "REDACT":
        return f"[REDACTED_{entity_up}]"
    if strategy == "FULL":
        return "*" * len(val)

    if entity_up == "EMAIL_ADDRESS":
        return mask_email(val, strategy)
    elif entity_up == "PHONE_NUMBER":
        return mask_phone(val, strategy)
    elif entity_up in ("PAN_NUMBER", "PAN"):
        return mask_pan(val, strategy)
    elif entity_up in ("AADHAAR_NUMBER", "AADHAAR"):
        return mask_aadhaar(val, strategy)
    elif entity_up in ("CREDIT_CARD", "IBAN_CODE"):
        return mask_credit_card(val, strategy)
    else:
        return mask_generic(val, entity_up, strategy)


def apply_masking_to_text(text: str, detections: List[Dict[str, Any]], default_strategy: str = "PARTIAL") -> str:
    """
    Applies masking to text for all detected PII entities.
    Processes spans in reverse order so character offsets remain exact!
    """
    sorted_dets = sorted(detections, key=lambda d: d["start"], reverse=True)
    result = text
    for d in sorted_dets:
        start = d["start"]
        end = d["end"]
        original = text[start:end]
        strategy = d.get("recommended_action", default_strategy)
        if strategy == "MASK":
            strategy = default_strategy
        masked = mask_entity_value(original, d["entity_type"], strategy)
        result = result[:start] + masked + result[end:]
    return result

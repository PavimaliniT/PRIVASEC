import re
import io
import json
import csv
from typing import List, Dict, Any, Optional, Tuple
from pypdf import PdfReader
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern, RecognizerResult
from presidio_anonymizer import AnonymizerEngine

# Indian PAN Pattern: 5 letters (first 3 alphabetic series, 4th status e.g. P/C/F/H/A/T, 5th first letter of surname), 4 digits, 1 letter
PAN_REGEX = r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"

# Aadhaar Pattern: 12 digits, cannot start with 0 or 1, optionally separated by spaces
AADHAAR_REGEX = r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b"

# API Secrets Pattern
API_KEY_REGEX = r"\b(sec_key_[0-9a-zA-Z]{24}|token_[0-9a-zA-Z]{36}|AIza[0-9A-Za-z\-_]{35}|[a-zA-Z0-9_\-]{20,64}_secret)\b"


def validate_pan(pan: str) -> bool:
    """Validates structure and common entity types of Indian PAN."""
    clean = pan.strip().upper()
    if not re.match(r"^[A-Z]{5}\d{4}[A-Z]$", clean):
        return False
    # 4th character typically denotes entity type (P=Person, C=Company, H=HUF, F=Firm, T=Trust, etc.)
    return clean[3] in "PCHFATBLJG"


def validate_aadhaar_structure(aadhaar: str) -> bool:
    """Validates structural constraints of 12-digit Indian Aadhaar."""
    clean = re.sub(r"\s+", "", aadhaar)
    if len(clean) != 12 or not clean.isdigit():
        return False
    if clean[0] in ('0', '1'):
        return False
    # Disallow trivial all-same sequences like 222222222222
    if len(set(clean)) == 1:
        return False
    return True


def luhn_checksum(card_number: str) -> bool:
    """Validates credit card numbers using Luhn checksum algorithm."""
    clean = re.sub(r"[\s\-]", "", card_number)
    if not clean.isdigit() or len(clean) < 13 or len(clean) > 19:
        return False
    digits = [int(d) for d in clean]
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += (doubled - 9) if doubled > 9 else doubled
        else:
            checksum += d
    return (checksum % 10) == 0


class PrivasecPIIDetector:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        self._register_custom_recognizers()

    def _register_custom_recognizers(self):
        # 1. Indian PAN Recognizer
        pan_pattern = Pattern(name="pan_pattern", regex=PAN_REGEX, score=0.90)
        pan_recognizer = PatternRecognizer(
            supported_entity="PAN_NUMBER",
            patterns=[pan_pattern],
            context=["pan", "income tax", "permanent account number", "card"]
        )
        self.analyzer.registry.add_recognizer(pan_recognizer)

        # 2. Aadhaar Recognizer
        aadhaar_pattern = Pattern(name="aadhaar_pattern", regex=AADHAAR_REGEX, score=0.88)
        aadhaar_recognizer = PatternRecognizer(
            supported_entity="AADHAAR_NUMBER",
            patterns=[aadhaar_pattern],
            context=["aadhaar", "uidai", "identity card", "unique id"]
        )
        self.analyzer.registry.add_recognizer(aadhaar_recognizer)

        # 3. Secret API Key Recognizer
        secret_pattern = Pattern(name="api_key_pattern", regex=API_KEY_REGEX, score=0.95)
        secret_recognizer = PatternRecognizer(
            supported_entity="SECRET_KEY",
            patterns=[secret_pattern],
            context=["api_key", "secret", "token", "auth_token", "private_key"]
        )
        self.analyzer.registry.add_recognizer(secret_recognizer)

    def scan_text(self, text: str, language: str = "en") -> List[Dict[str, Any]]:
        """
        Scans text for sensitive PII entities, validates candidates,
        and returns enriched results with recommended treatments.
        """
        if not text or not text.strip():
            return []

        results: List[RecognizerResult] = self.analyzer.analyze(
            text=text,
            language=language,
            entities=[
                "EMAIL_ADDRESS",
                "PHONE_NUMBER",
                "PERSON",
                "LOCATION",
                "CREDIT_CARD",
                "IP_ADDRESS",
                "DATE_TIME",
                "PAN_NUMBER",
                "AADHAAR_NUMBER",
                "SECRET_KEY"
            ]
        )

        detections = []
        for r in results:
            val = text[r.start:r.end]
            confidence = r.score
            is_valid = True

            # Domain specific candidate validation
            if r.entity_type == "PAN_NUMBER":
                if not validate_pan(val):
                    confidence *= 0.6
                    is_valid = False
            elif r.entity_type == "AADHAAR_NUMBER":
                if not validate_aadhaar_structure(val):
                    confidence *= 0.6
                    is_valid = False
            elif r.entity_type == "CREDIT_CARD":
                if not luhn_checksum(val):
                    confidence *= 0.5
                    is_valid = False

            # Recommended treatment based on entity sensitivity
            if r.entity_type in ("CREDIT_CARD", "SECRET_KEY"):
                action = "REDACT"
            elif r.entity_type in ("PAN_NUMBER", "AADHAAR_NUMBER", "EMAIL_ADDRESS", "PHONE_NUMBER"):
                action = "MASK"
            elif r.entity_type in ("PERSON", "IP_ADDRESS"):
                action = "PSEUDONYMIZE"
            else:
                action = "MASK"

            detections.append({
                "entity_type": r.entity_type,
                "confidence": round(confidence, 2),
                "start": r.start,
                "end": r.end,
                "text_sample": val,
                "is_validated": is_valid,
                "recommended_action": action
            })

        # Sort by starting offset
        detections.sort(key=lambda x: x["start"])
        return detections

    def scan_file_content(self, filename: str, content: bytes) -> Tuple[str, List[Dict[str, Any]]]:
        """Extracts text from supported file types (TXT, CSV, JSON, PDF) and scans for PII."""
        ext = filename.lower().split(".")[-1]
        extracted_text = ""

        if ext in ("txt", "log", "md"):
            extracted_text = content.decode("utf-8", errors="replace")
        elif ext == "csv":
            try:
                reader = csv.reader(io.StringIO(content.decode("utf-8", errors="replace")))
                rows = [" ".join(row) for row in reader]
                extracted_text = "\n".join(rows)
            except Exception:
                extracted_text = content.decode("utf-8", errors="replace")
        elif ext == "json":
            try:
                parsed = json.loads(content.decode("utf-8", errors="replace"))
                extracted_text = json.dumps(parsed, indent=2)
            except Exception:
                extracted_text = content.decode("utf-8", errors="replace")
        elif ext == "pdf":
            try:
                reader = PdfReader(io.BytesIO(content))
                pages_text = []
                for p in reader.pages:
                    t = p.extract_text()
                    if t:
                        pages_text.append(t)
                extracted_text = "\n".join(pages_text)
            except Exception as e:
                extracted_text = f"Error reading PDF content: {str(e)}"
        else:
            extracted_text = content.decode("utf-8", errors="replace")

        detections = self.scan_text(extracted_text)
        return extracted_text, detections


pii_detector = PrivasecPIIDetector()
